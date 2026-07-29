from flask import Blueprint, render_template, request, redirect, url_for, flash, session, Response
from models.database import db
from models.user import User, Role
from models.candidate import CandidateProfile
from models.interview import JobPosting, InterviewSession
from models.mcq import McqTest, Question, TestSession
from models.activity_log import ActivityLog
from services.report_service import ReportService
from routes.auth_routes import role_required

recruiter_bp = Blueprint("recruiter", __name__, url_prefix="/recruiter")

@recruiter_bp.route("/dashboard")
@role_required(Role.RECRUITER)
def dashboard():
    recruiter = db.session.get(User, session["user_id"])
    if not recruiter:
        session.clear()
        flash("Session expired. Please log in again.", "warning")
        return redirect(url_for("auth.login"))

    jobs = JobPosting.query.filter_by(recruiter_id=recruiter.id).all()
    candidates = CandidateProfile.query.order_by(CandidateProfile.resume_score.desc()).all()
    
    total_candidates = len(candidates)
    
    active_sessions_list = InterviewSession.query.filter_by(status="in_progress").order_by(InterviewSession.created_at.desc()).all()
    active_interviews = len(active_sessions_list)

    completed_sessions_list = InterviewSession.query.filter_by(status="completed").order_by(InterviewSession.completed_at.desc()).all()
    completed_interviews = len(completed_sessions_list)

    avg_resume_score = db.session.query(db.func.avg(CandidateProfile.resume_score)).scalar() or 0.0

    recent_sessions = InterviewSession.query.order_by(InterviewSession.created_at.desc()).limit(10).all()
    recent_activities = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(10).all()

    return render_template(
        "recruiter/dashboard.html",
        recruiter=recruiter,
        jobs=jobs,
        candidates=candidates,
        active_sessions_list=active_sessions_list,
        completed_sessions_list=completed_sessions_list,
        recent_sessions=recent_sessions,
        recent_activities=recent_activities,
        total_candidates=total_candidates,
        active_interviews=active_interviews,
        completed_interviews=completed_interviews,
        avg_resume_score=round(avg_resume_score, 1)
    )

@recruiter_bp.route("/candidates")
@role_required(Role.RECRUITER)
def candidates():
    min_score = request.args.get("min_score", type=int, default=0)
    skill_filter = request.args.get("skill", "").strip().lower()
    search_query = request.args.get("q", "").strip().lower()
    exp_filter = request.args.get("exp", "").strip()
    role_filter = request.args.get("target_role", "").strip().lower()
    status_filter = request.args.get("status", "").strip().lower()
    edu_filter = request.args.get("education", "").strip().lower()

    query = db.session.query(CandidateProfile).join(User)

    if min_score > 0:
        query = query.filter(CandidateProfile.resume_score >= min_score)

    if search_query:
        query = query.filter((User.name.ilike(f"%{search_query}%")) | (User.email.ilike(f"%{search_query}%")) | (User.target_role.ilike(f"%{search_query}%")))

    if role_filter:
        query = query.filter(User.target_role.ilike(f"%{role_filter}%"))

    if edu_filter:
        query = query.filter(CandidateProfile.education.ilike(f"%{edu_filter}%"))

    if exp_filter:
        if exp_filter == "0-2":
            query = query.filter(CandidateProfile.experience_years <= 2.0)
        elif exp_filter == "2-5":
            query = query.filter(CandidateProfile.experience_years > 2.0, CandidateProfile.experience_years <= 5.0)
        elif exp_filter == "5+":
            query = query.filter(CandidateProfile.experience_years > 5.0)

    all_profiles = query.order_by(CandidateProfile.resume_score.desc()).all()

    if skill_filter:
        all_profiles = [p for p in all_profiles if any(skill_filter in s.lower() for s in p.parsed_skills)]

    # Overall Summary Metrics for Top Cards
    total_candidates = CandidateProfile.query.count()
    shortlisted_count = CandidateProfile.query.filter(CandidateProfile.resume_score >= 80.0).count()
    pending_count = CandidateProfile.query.filter(CandidateProfile.resume_score < 80.0).count()
    avg_resume_score = db.session.query(db.func.avg(CandidateProfile.resume_score)).scalar() or 0.0

    return render_template(
        "recruiter/candidates.html",
        candidates=all_profiles,
        total_candidates=total_candidates,
        shortlisted_count=shortlisted_count,
        pending_count=pending_count,
        avg_resume_score=round(avg_resume_score, 1),
        min_score=min_score,
        skill_filter=skill_filter,
        search_query=search_query,
        exp_filter=exp_filter,
        role_filter=role_filter,
        status_filter=status_filter,
        edu_filter=edu_filter
    )

@recruiter_bp.route("/candidate/<int:user_id>")
@role_required(Role.RECRUITER)
def candidate_detail(user_id):
    candidate_user = db.session.get(User, user_id)
    if not candidate_user:
        flash("Candidate not found.", "danger")
        return redirect(url_for("recruiter.candidates"))

    profile = candidate_user.candidate_profile
    interviews = InterviewSession.query.filter_by(candidate_id=user_id).order_by(InterviewSession.created_at.desc()).all()
    mcq_results = TestSession.query.filter_by(candidate_id=user_id).order_by(TestSession.completed_at.desc()).all()

    return render_template(
        "recruiter/candidate_detail.html",
        candidate_user=candidate_user,
        profile=profile,
        interviews=interviews,
        mcq_results=mcq_results
    )

@recruiter_bp.route("/jobs", methods=["GET", "POST"])
@role_required(Role.RECRUITER)
def jobs():
    recruiter_id = session["user_id"]
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        role_type = request.form.get("role_type", "Python Developer").strip()
        description = request.form.get("description", "").strip()
        skills_str = request.form.get("skills_required", "")
        experience_level = request.form.get("experience_level", "Mid Level")
        difficulty = request.form.get("difficulty", "Medium")
        pass_score = int(request.form.get("pass_score", 70))
        interview_type = request.form.get("interview_type", "Technical")
        total_questions = int(request.form.get("total_questions", 20))
        time_limit = int(request.form.get("time_limit", 45))

        if not title or not description:
            flash("Job title and description are required.", "danger")
            return redirect(url_for("recruiter.jobs"))

        skills_list = [s.strip() for s in skills_str.split(",") if s.strip()]

        job = JobPosting(
            recruiter_id=recruiter_id,
            title=title,
            role_type=role_type,
            description=description,
            experience_level=experience_level,
            difficulty=difficulty,
            pass_score=pass_score,
            interview_type=interview_type,
            total_questions=total_questions,
            time_limit=time_limit
        )
        job.skills_required = skills_list
        db.session.add(job)
        db.session.commit()

        log = ActivityLog(user_id=recruiter_id, action="Created Job Posting", details=f"Title: {title}")
        db.session.add(log)
        db.session.commit()

        flash("Job posting created successfully!", "success")
        return redirect(url_for("recruiter.jobs"))

    my_jobs = JobPosting.query.filter_by(recruiter_id=recruiter_id).order_by(JobPosting.created_at.desc()).all()
    all_candidates = User.query.filter_by(role=Role.CANDIDATE).order_by(User.name.asc()).all()
    return render_template("recruiter/jobs.html", jobs=my_jobs, candidates=all_candidates)

@recruiter_bp.route("/jobs/edit/<int:job_id>", methods=["POST"])
@role_required(Role.RECRUITER)
def edit_job(job_id):
    job = db.session.get(JobPosting, job_id)
    if not job or job.recruiter_id != session["user_id"]:
        flash("Unauthorized action.", "danger")
        return redirect(url_for("recruiter.jobs"))

    job.title = request.form.get("title", job.title).strip()
    job.role_type = request.form.get("role_type", job.role_type).strip()
    job.description = request.form.get("description", job.description).strip()
    skills_str = request.form.get("skills_required", "")
    if skills_str:
        job.skills_required = [s.strip() for s in skills_str.split(",") if s.strip()]
    job.experience_level = request.form.get("experience_level", job.experience_level)
    job.difficulty = request.form.get("difficulty", job.difficulty)
    job.pass_score = int(request.form.get("pass_score", job.pass_score))
    job.interview_type = request.form.get("interview_type", job.interview_type)
    job.total_questions = int(request.form.get("total_questions", job.total_questions))
    job.time_limit = int(request.form.get("time_limit", job.time_limit))

    db.session.commit()
    flash("Job posting updated successfully!", "success")
    return redirect(url_for("recruiter.jobs"))

@recruiter_bp.route("/jobs/delete/<int:job_id>", methods=["POST"])
@role_required(Role.RECRUITER)
def delete_job(job_id):
    job = db.session.get(JobPosting, job_id)
    if not job or job.recruiter_id != session["user_id"]:
        flash("Unauthorized action.", "danger")
        return redirect(url_for("recruiter.jobs"))

    db.session.delete(job)
    db.session.commit()
    flash("Job posting deleted.", "info")
    return redirect(url_for("recruiter.jobs"))

@recruiter_bp.route("/mcq", methods=["GET", "POST"])
@role_required(Role.RECRUITER)
def mcq():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        category = request.form.get("category", "Python").strip()
        total_questions = int(request.form.get("total_questions", 20))
        duration_minutes = int(request.form.get("duration_minutes", 15))
        difficulty = request.form.get("difficulty", "Medium")
        passing_marks = int(request.form.get("passing_marks", 70))
        attempts_allowed = int(request.form.get("attempts_allowed", 3))
        shuffle_questions = bool(request.form.get("shuffle_questions"))
        negative_marking = bool(request.form.get("negative_marking"))

        test = McqTest(
            title=title,
            category=category,
            total_questions=total_questions,
            duration_minutes=duration_minutes,
            difficulty=difficulty,
            passing_marks=passing_marks,
            attempts_allowed=attempts_allowed,
            shuffle_questions=shuffle_questions,
            negative_marking=negative_marking,
            created_by=session["user_id"]
        )
        db.session.add(test)
        db.session.commit()

        flash("MCQ Test created successfully!", "success")
        return redirect(url_for("recruiter.mcq"))

    tests = McqTest.query.order_by(McqTest.created_at.desc()).all()
    
    # Enrich tests with Candidates Attempted count and Average Score
    enriched_tests = []
    for t in tests:
        test_sessions = TestSession.query.filter_by(test_id=t.id).all()
        attempted_count = len(test_sessions)
        avg_score = round(sum(s.score for s in test_sessions) / attempted_count, 1) if attempted_count > 0 else 0.0
        enriched_tests.append({
            "test": t,
            "attempted_count": attempted_count,
            "avg_score": avg_score
        })

    return render_template("recruiter/mcq.html", enriched_tests=enriched_tests)

@recruiter_bp.route("/reports")
@role_required(Role.RECRUITER)
def reports():
    candidates = CandidateProfile.query.join(User).order_by(User.name.asc()).all()
    recent_exports = [
        {"report_name": "Overall Candidates Analytics Summary", "format": "PDF", "type": "Candidate", "date": "2026-07-28 19:40"},
        {"report_name": "AI Mock Interview Score Distribution", "format": "CSV", "type": "Interview", "date": "2026-07-28 18:15"},
        {"report_name": "MCQ Skill Test Results Matrix", "format": "Excel", "type": "MCQ", "date": "2026-07-27 14:20"}
    ]
    return render_template("recruiter/reports.html", candidates=candidates, recent_exports=recent_exports)

@recruiter_bp.route("/export/<format_type>")
@role_required(Role.RECRUITER)
def export_candidates(format_type):
    report_type = request.args.get("report_type", "candidates")
    candidates = db.session.query(CandidateProfile).join(User).all()
    
    data = []
    for c in candidates:
        data.append({
            "Candidate ID": c.user_id,
            "Name": c.user.name,
            "Email": c.user.email,
            "Target Role": c.user.target_role,
            "Resume Score": c.resume_score,
            "Experience (Years)": c.experience_years,
            "Education": c.education,
            "Skills": ", ".join(c.parsed_skills)
        })

    if format_type == "pdf":
        cand_dict = {
            "name": "Enterprise Candidates Overview",
            "email": "recruiter@interviewai.com",
            "target_role": "Python & Data Science Stack",
            "resume_score": round(sum(c['Resume Score'] for c in data) / len(data), 1) if data else 0,
            "experience_years": 3.5,
            "education": "Top Tier Engineering Universities",
            "parsed_skills": ["Python", "SQL", "Flask", "REST API", "JavaScript"],
            "missing_skills": ["Docker", "Kubernetes"]
        }
        pdf_bytes = ReportService.generate_candidate_pdf(cand_dict)
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={"Content-Disposition": f"attachment;filename=InterviewAI_{report_type.capitalize()}_Report.pdf"}
        )
    elif format_type == "csv":
        csv_data = ReportService.export_candidates_csv(data)
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename=InterviewAI_{report_type.capitalize()}_Report.csv"}
        )
    elif format_type == "excel":
        excel_data = ReportService.export_candidates_excel(data)
        return Response(
            excel_data,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment;filename=InterviewAI_{report_type.capitalize()}_Report.xlsx"}
        )
    else:
        flash("Invalid export format.", "danger")
        return redirect(url_for("recruiter.reports"))
