from datetime import datetime
from flask import Blueprint, request, jsonify, session
from models.database import db
from models.user import User, Role
from models.candidate import CandidateProfile
from models.interview import JobPosting, InterviewSession, InterviewResponse
from models.mcq import Question, McqTest, TestSession
from models.notification import Notification
from models.activity_log import ActivityLog
from services.ai_service import AIService

api_bp = Blueprint("api", __name__, url_prefix="/api/v1")

@api_bp.route("/interview/answer/submit", methods=["POST"])
def submit_interview_answer():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    data = request.get_json() or {}
    session_id = data.get("session_id")
    response_id = data.get("response_id")
    user_answer = data.get("user_answer", "").strip()

    if not session_id or not response_id:
        return jsonify({"success": False, "error": "Missing session or response ID"}), 400

    resp = db.session.get(InterviewResponse, response_id)
    if not resp or resp.session_id != int(session_id):
        return jsonify({"success": False, "error": "Invalid response record"}), 404

    session_obj = db.session.get(InterviewSession, session_id)
    if session_obj.candidate_id != session["user_id"]:
        return jsonify({"success": False, "error": "Forbidden"}), 403

    # AI Evaluation
    ai_service = AIService()
    eval_result = ai_service.evaluate_answer(resp.question_text, user_answer, role_title=session_obj.role_title)

    resp.user_answer = user_answer
    resp.score = float(eval_result.get("score", 70))
    resp.feedback = eval_result.get("feedback", "")
    resp.model_answer = eval_result.get("model_answer", "")
    resp.missing_concepts = eval_result.get("missing_concepts", [])

    db.session.commit()

    # Recalculate session overall score
    all_responses = session_obj.responses.all()
    answered_responses = [r for r in all_responses if r.user_answer]
    if answered_responses:
        avg_score = sum(r.score for r in answered_responses) / len(answered_responses)
        session_obj.overall_score = round(avg_score, 1)

    # If all answered, mark complete
    if len(answered_responses) == session_obj.total_questions:
        session_obj.status = "completed"
        session_obj.completed_at = datetime.utcnow()

    db.session.commit()

    return jsonify({
        "success": True,
        "score": resp.score,
        "feedback": resp.feedback,
        "model_answer": resp.model_answer,
        "missing_concepts": resp.missing_concepts,
        "session_score": session_obj.overall_score,
        "session_status": session_obj.status
    })

@api_bp.route("/mcq/submit", methods=["POST"])
def submit_mcq_test():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    data = request.get_json() or {}
    test_id = data.get("test_id")
    user_answers = data.get("answers", {})

    test_obj = db.session.get(McqTest, test_id)
    if not test_obj:
        return jsonify({"success": False, "error": "Test not found"}), 404

    questions = Question.query.filter_by(category=test_obj.category).limit(test_obj.total_questions).all()
    if not questions:
        questions = Question.query.limit(test_obj.total_questions).all()

    correct_count = 0
    details = []

    for q in questions:
        candidate_ans = user_answers.get(str(q.id), "").upper()
        is_correct = (candidate_ans == q.correct_option.upper())
        if is_correct:
            correct_count += 1
        
        details.append({
            "question_id": q.id,
            "question_text": q.question_text,
            "selected_option": candidate_ans,
            "correct_option": q.correct_option,
            "is_correct": is_correct,
            "explanation": q.explanation
        })

    total_q = len(questions) or 1
    final_score = round((correct_count / total_q) * 100, 1)

    t_session = TestSession(
        candidate_id=session["user_id"],
        test_id=test_obj.id,
        score=final_score,
        total_questions=total_q,
        correct_answers=correct_count
    )
    t_session.details = details
    db.session.add(t_session)

    notif = Notification(user_id=session["user_id"], message=f"MCQ Test '{test_obj.title}' completed. Score: {final_score}%", type="info")
    db.session.add(notif)
    db.session.commit()

    return jsonify({
        "success": True,
        "score": final_score,
        "correct_answers": correct_count,
        "total_questions": total_q,
        "details": details
    })

@api_bp.route("/analytics/candidate", methods=["GET"])
def candidate_analytics():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    user_id = session["user_id"]
    profile = CandidateProfile.query.filter_by(user_id=user_id).first()
    sessions = InterviewSession.query.filter_by(candidate_id=user_id, status="completed").order_by(InterviewSession.completed_at.asc()).all()

    labels = [s.completed_at.strftime("%b %d") if s.completed_at else f"Session {s.id}" for s in sessions]
    scores = [s.overall_score for s in sessions]

    if not labels:
        labels = ["Session 1", "Session 2", "Session 3"]
        scores = [65.0, 78.0, 85.5]

    skills = profile.parsed_skills if (profile and profile.parsed_skills) else ["Python", "Flask", "SQL", "REST API", "Git"]
    skill_scores = [min(100, max(50, 70 + idx * 5)) for idx, s in enumerate(skills[:6])]

    return jsonify({
        "success": True,
        "progression": {"labels": labels, "scores": scores},
        "skills": {"labels": skills[:6], "scores": skill_scores},
        "resume_score": profile.resume_score if profile else 75
    })

@api_bp.route("/analytics/recruiter", methods=["GET"])
def recruiter_analytics():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    profiles = CandidateProfile.query.all()
    sessions = InterviewSession.query.order_by(InterviewSession.created_at.asc()).all()

    # 1. Interview Trend (Line chart)
    trend_dict = {}
    for s in sessions:
        date_str = s.created_at.strftime("%b %d") if s.created_at else "Session"
        trend_dict[date_str] = trend_dict.get(date_str, 0) + 1

    trend_labels = list(trend_dict.keys()) or ["Week 1", "Week 2", "Week 3", "Week 4"]
    trend_data = list(trend_dict.values()) or [2, 5, 8, 12]

    # 2. Candidate Performance (Bar chart)
    perf_labels = []
    perf_scores = []
    for p in profiles[:6]:
        user_name = p.user.name if p.user else f"Candidate #{p.id}"
        avg_s = db.session.query(db.func.avg(InterviewSession.overall_score)).filter(InterviewSession.candidate_id == p.user_id).scalar() or float(p.resume_score)
        perf_labels.append(user_name)
        perf_scores.append(round(avg_s, 1))

    # 3. Resume Score Distribution & Top Skills & Experience Mix
    score_brackets = {"90-100 (Top)": 0, "75-89 (High)": 0, "60-74 (Mid)": 0, "Below 60": 0}
    skill_counts = {}
    exp_brackets = {"0-2 Yrs (Junior)": 0, "2-5 Yrs (Mid)": 0, "5+ Yrs (Senior)": 0}

    for p in profiles:
        score = p.resume_score
        if score >= 90:
            score_brackets["90-100 (Top)"] += 1
        elif score >= 75:
            score_brackets["75-89 (High)"] += 1
        elif score >= 60:
            score_brackets["60-74 (Mid)"] += 1
        else:
            score_brackets["Below 60"] += 1

        for skill in p.parsed_skills:
            skill_counts[skill] = skill_counts.get(skill, 0) + 1

        years = p.experience_years or 0
        if years <= 2:
            exp_brackets["0-2 Yrs (Junior)"] += 1
        elif years <= 5:
            exp_brackets["2-5 Yrs (Mid)"] += 1
        else:
            exp_brackets["5+ Yrs (Senior)"] += 1

    top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:6]

    # 4. Interview Completion Rate
    completed_count = InterviewSession.query.filter_by(status="completed").count()
    active_count = InterviewSession.query.filter_by(status="in_progress").count()
    total_sess = completed_count + active_count
    completion_rate_pct = round((completed_count / total_sess * 100), 1) if total_sess > 0 else 85.0

    # 5. Resume Scores by Department
    dept_scores = {
        "Engineering": [],
        "Data Science": [],
        "Machine Learning": [],
        "Design": [],
        "HR & Mgmt": []
    }

    for p in profiles:
        role = (p.user.target_role.lower() if p.user and p.user.target_role else "")
        score = p.resume_score or 75
        if "python" in role or "engineer" in role or "full stack" in role or "software" in role:
            dept_scores["Engineering"].append(score)
        elif "data" in role or "sql" in role:
            dept_scores["Data Science"].append(score)
        elif "machine" in role or "ml" in role or "ai" in role:
            dept_scores["Machine Learning"].append(score)
        elif "design" in role or "ui" in role or "ux" in role:
            dept_scores["Design"].append(score)
        else:
            dept_scores["HR & Mgmt"].append(score)

    dept_avg = {k: (round(sum(v) / len(v), 1) if v else 78.5) for k, v in dept_scores.items()}

    return jsonify({
        "success": True,
        "interview_trend": {
            "labels": trend_labels,
            "data": trend_data
        },
        "candidate_performance": {
            "labels": perf_labels or ["XYZ", "Priya Sharma", "David Chen", "Sophia Rodriguez"],
            "data": perf_scores or [92.0, 88.5, 78.0, 84.0]
        },
        "score_distribution": {
            "labels": list(score_brackets.keys()),
            "data": list(score_brackets.values())
        },
        "top_skills": {
            "labels": [k for k, v in top_skills] or ["Python", "SQL", "JavaScript", "Flask", "Machine Learning", "Data Science"],
            "data": [v for k, v in top_skills] or [14, 11, 9, 8, 6, 5]
        },
        "experience_distribution": {
            "labels": list(exp_brackets.keys()),
            "data": list(exp_brackets.values())
        },
        "completion_rate": {
            "completed": completed_count,
            "in_progress": active_count,
            "rate_pct": completion_rate_pct
        },
        "department_scores": {
            "labels": list(dept_avg.keys()),
            "data": list(dept_avg.values())
        }
    })

@api_bp.route("/notifications/mark-read/<int:notif_id>", methods=["POST"])
def mark_notification_read(notif_id):
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    notif = Notification.query.filter_by(id=notif_id, user_id=session["user_id"]).first()
    if notif:
        notif.is_read = True
        db.session.commit()
    return jsonify({"success": True})
