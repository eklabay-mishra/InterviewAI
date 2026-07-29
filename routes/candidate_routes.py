import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, jsonify, Response
from werkzeug.utils import secure_filename
from models.database import db
from models.user import User, Role
from models.candidate import CandidateProfile
from models.interview import JobPosting, InterviewSession, InterviewResponse
from models.mcq import McqTest, Question, TestSession
from models.notification import Notification
from models.activity_log import ActivityLog
from services.resume_parser import ResumeParser
from services.ai_service import AIService
from services.report_service import ReportService
from routes.auth_routes import role_required

candidate_bp = Blueprint("candidate", __name__, url_prefix="/candidate")

@candidate_bp.route("/dashboard")
@role_required(Role.CANDIDATE)
def dashboard():
    user = db.session.get(User, session["user_id"])
    profile = user.candidate_profile
    if not profile:
        profile = CandidateProfile(user_id=user.id)
        db.session.add(profile)
        db.session.commit()

    recent_sessions = InterviewSession.query.filter_by(candidate_id=user.id).order_by(InterviewSession.created_at.desc()).limit(5).all()
    
    # Calculate stats
    total_interviews = InterviewSession.query.filter_by(candidate_id=user.id).count()
    avg_score = db.session.query(db.func.avg(InterviewSession.overall_score)).filter(InterviewSession.candidate_id == user.id, InterviewSession.status == "completed").scalar() or 0.0

    # Compact Notifications (limit 3)
    user_notifications = Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).limit(3).all()

    # Calculate Profile Completion %
    completion_items = [
        bool(user.name),
        bool(user.email),
        bool(user.target_role),
        bool(user.bio),
        bool(profile.resume_filename),
        bool(profile.experience_years > 0),
        bool(profile.education),
        bool(len(profile.parsed_skills) > 0),
        bool(len(profile.projects) > 0),
        bool(profile.github or profile.linkedin)
    ]
    completion_pct = int((sum(1 for item in completion_items if item) / len(completion_items)) * 100)

    resume_last_updated = profile.uploaded_at.strftime("%b %d, %Y") if profile.uploaded_at else "Not uploaded yet"

    return render_template(
        "candidate/dashboard.html",
        user=user,
        profile=profile,
        recent_sessions=recent_sessions,
        user_notifications=user_notifications,
        total_interviews=total_interviews,
        avg_score=round(avg_score, 1),
        profile_completion=completion_pct,
        resume_last_updated=resume_last_updated
    )

@candidate_bp.route("/resume-analyzer", methods=["GET", "POST"])
@role_required(Role.CANDIDATE)
def resume_analyzer():
    user = db.session.get(User, session["user_id"])
    profile = user.candidate_profile or CandidateProfile(user_id=user.id)

    if request.method == "POST":
        if "resume_file" not in request.files:
            flash("No file selected for upload.", "warning")
            return redirect(request.url)

        file = request.files["resume_file"]
        if file.filename == "":
            flash("No file selected.", "warning")
            return redirect(request.url)

        filename = secure_filename(file.filename)
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in [".pdf", ".docx", ".txt"]:
            flash("Only PDF, DOCX, and TXT resume files are allowed.", "danger")
            return redirect(request.url)

        upload_folder = current_app.config.get("UPLOAD_FOLDER", "uploads/resumes")
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, f"user_{user.id}_{filename}")
        file.save(file_path)

        # Parse Text & Run AI Analysis
        try:
            raw_text = ResumeParser.extract_text(file_path)
            ai_service = AIService()
            analysis = ai_service.analyze_resume(raw_text, target_role=user.target_role or "Python Full Stack Developer")

            profile.resume_filename = filename
            profile.resume_path = file_path
            profile.resume_score = analysis.get("resume_score", 70)
            profile.experience_years = analysis.get("experience_years", 1.0)
            profile.education = analysis.get("education", "B.S. Computer Science")
            profile.summary = analysis.get("summary", "")
            profile.parsed_skills = analysis.get("parsed_skills", [])
            profile.missing_skills = analysis.get("missing_skills", [])
            profile.analysis_data = analysis
            profile.uploaded_at = datetime.utcnow()

            db.session.commit()

            notif = Notification(user_id=user.id, message=f"Resume analysis complete. Your Resume Score is {profile.resume_score}/100.", type="success")
            log = ActivityLog(user_id=user.id, action="Resume Uploaded & Analyzed", details=f"Score: {profile.resume_score}, File: {filename}")
            db.session.add(notif)
            db.session.add(log)
            db.session.commit()

            flash("Resume analyzed successfully!", "success")
        except Exception as e:
            flash(f"Error analyzing resume: {str(e)}", "danger")

        return redirect(url_for("candidate.resume_analyzer"))

    return render_template("candidate/resume_analyzer.html", user=user, profile=profile)

@candidate_bp.route("/mock-interview")
@role_required(Role.CANDIDATE)
def mock_interview():
    user = db.session.get(User, session["user_id"])
    sessions = InterviewSession.query.filter_by(candidate_id=user.id).order_by(InterviewSession.created_at.desc()).all()
    return render_template("candidate/mock_interview.html", user=user, sessions=sessions)

@candidate_bp.route("/mock-interview/start", methods=["POST"])
@role_required(Role.CANDIDATE)
def start_mock_interview():
    user = db.session.get(User, session["user_id"])
    category = request.form.get("category", "Python")
    target_role = request.form.get("target_role", user.target_role or "Python Full Stack Developer")
    difficulty = request.form.get("difficulty", "Medium")
    num_questions = int(request.form.get("num_questions", "20"))
    duration_minutes = int(request.form.get("duration", "30"))

    role_title = f"{category} - {target_role}"
    if category == "HR" or "hr" in target_role.lower():
        candidate_skills = ["HR Management", "Behavioral Interviewing", "Talent Acquisition", "Employee Relations", "Performance Management"]
    else:
        candidate_skills = user.candidate_profile.parsed_skills if (user.candidate_profile and user.candidate_profile.parsed_skills) else ["Python", "Flask", "SQL"]

    # Generate interview questions via AI Service
    ai_service = AIService()
    questions_data = ai_service.generate_interview_questions(role_title, candidate_skills, difficulty=difficulty, count=num_questions)

    # Create Session
    session_obj = InterviewSession(
        candidate_id=user.id,
        role_title=role_title,
        total_questions=len(questions_data),
        status="in_progress"
    )
    db.session.add(session_obj)
    db.session.commit()

    # Create Response objects for questions
    for idx, q in enumerate(questions_data, start=1):
        resp = InterviewResponse(
            session_id=session_obj.id,
            question_number=idx,
            question_text=q.get("question_text", "Explain core technical concepts."),
            category=q.get("category", category)
        )
        db.session.add(resp)
    
    db.session.commit()

    log = ActivityLog(user_id=user.id, action="Started AI Mock Interview", details=f"Session ID: {session_obj.id}, Role: {role_title}")
    db.session.add(log)
    db.session.commit()

    return redirect(url_for("candidate.interview_session", session_id=session_obj.id))

@candidate_bp.route("/mock-interview/session/<int:session_id>")
@role_required(Role.CANDIDATE)
def interview_session(session_id):
    user = db.session.get(User, session["user_id"])
    session_obj = InterviewSession.query.filter_by(id=session_id, candidate_id=user.id).first_or_404()
    responses = session_obj.responses.order_by(InterviewResponse.question_number.asc()).all()
    return render_template("candidate/interview_session.html", session_obj=session_obj, responses=responses)

@candidate_bp.route("/mcq-tests")
@role_required(Role.CANDIDATE)
def mcq_tests():
    user = db.session.get(User, session["user_id"])
    tests = McqTest.query.order_by(McqTest.created_at.desc()).all()
    my_sessions = TestSession.query.filter_by(candidate_id=user.id).order_by(TestSession.completed_at.desc()).all()
    return render_template("candidate/mcq_tests.html", user=user, tests=tests, my_sessions=my_sessions)

@candidate_bp.route("/mcq-tests/<int:test_id>")
@role_required(Role.CANDIDATE)
def take_mcq_test(test_id):
    test_obj = McqTest.query.get_or_404(test_id)
    questions = Question.query.filter_by(category=test_obj.category).limit(test_obj.total_questions).all()
    if not questions:
        questions = Question.query.limit(test_obj.total_questions).all()
    return render_template("candidate/take_mcq_test.html", test_obj=test_obj, questions=questions)

@candidate_bp.route("/history")
@role_required(Role.CANDIDATE)
def history():
    user = db.session.get(User, session["user_id"])
    
    q = request.args.get("q", "").strip().lower()
    cat_filter = request.args.get("category", "").strip().lower()

    # Query Interview Sessions
    i_query = InterviewSession.query.filter_by(candidate_id=user.id)
    if cat_filter and cat_filter != "all":
        i_query = i_query.filter(InterviewSession.role_title.ilike(f"%{cat_filter}%"))
    sessions = i_query.order_by(InterviewSession.created_at.desc()).all()

    if q:
        sessions = [s for s in sessions if q in s.role_title.lower() or q in s.status.lower()]

    # Query MCQ Sessions
    mcq_sessions = TestSession.query.filter_by(candidate_id=user.id).order_by(TestSession.completed_at.desc()).all()
    if q:
        mcq_sessions = [m for m in mcq_sessions if m.test and q in m.test.title.lower()]

    # Summary Card Metrics
    total_interviews = len(sessions)
    avg_score = db.session.query(db.func.avg(InterviewSession.overall_score)).filter(InterviewSession.candidate_id == user.id, InterviewSession.status == "completed").scalar() or 0.0
    highest_score = db.session.query(db.func.max(InterviewSession.overall_score)).filter(InterviewSession.candidate_id == user.id).scalar() or 0.0
    total_mcqs = len(mcq_sessions)

    return render_template(
        "candidate/history.html",
        user=user,
        sessions=sessions,
        mcq_sessions=mcq_sessions,
        total_interviews=total_interviews,
        avg_score=round(avg_score, 1),
        highest_score=round(highest_score, 1),
        total_mcqs=total_mcqs,
        search_query=q,
        selected_category=cat_filter
    )

@candidate_bp.route("/report/pdf")
@role_required(Role.CANDIDATE)
def download_pdf_report():
    user = db.session.get(User, session["user_id"])
    profile = user.candidate_profile
    sessions = InterviewSession.query.filter_by(candidate_id=user.id).order_by(InterviewSession.created_at.desc()).limit(10).all()

    c_data = {
        "name": user.name,
        "email": user.email,
        "target_role": user.target_role,
        "resume_score": profile.resume_score if profile else 0,
        "experience_years": profile.experience_years if profile else 0,
        "education": profile.education if profile else "N/A",
        "parsed_skills": profile.parsed_skills if profile else [],
        "missing_skills": profile.missing_skills if profile else []
    }
    i_data = [s.to_dict() for s in sessions]

    pdf_bytes = ReportService.generate_candidate_pdf(c_data, i_data)
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment;filename=InterviewAI_Report_{user.name.replace(' ', '_')}.pdf"}
    )

@candidate_bp.route("/profile", methods=["GET", "POST"])
@role_required(Role.CANDIDATE)
def profile():
    user = db.session.get(User, session["user_id"])
    profile = user.candidate_profile or CandidateProfile(user_id=user.id)

    if request.method == "POST":
        user.name = request.form.get("name", user.name).strip()
        user.target_role = request.form.get("target_role", user.target_role).strip()
        user.bio = request.form.get("bio", user.bio).strip()

        profile.phone = request.form.get("phone", profile.phone).strip()
        profile.education = request.form.get("education", profile.education).strip()
        profile.graduation_year = request.form.get("graduation_year", profile.graduation_year).strip()
        profile.github = request.form.get("github", profile.github).strip()
        profile.linkedin = request.form.get("linkedin", profile.linkedin).strip()
        profile.portfolio = request.form.get("portfolio", profile.portfolio).strip()

        skills_raw = request.form.get("skills", "")
        if skills_raw:
            profile.parsed_skills = [s.strip() for s in skills_raw.split(",") if s.strip()]

        try:
            profile.experience_years = float(request.form.get("experience_years", profile.experience_years))
        except ValueError:
            pass

        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("candidate.profile"))

    return render_template("candidate/profile.html", user=user, profile=profile)
