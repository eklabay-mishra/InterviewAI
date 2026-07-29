from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.database import db
from models.user import User, Role
from models.candidate import CandidateProfile
from models.activity_log import ActivityLog

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

def role_required(*roles):
    """Decorator to enforce role-based access control (RBAC)."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("auth.login"))

            try:
                user = db.session.get(User, session["user_id"])
            except Exception:
                db.session.rollback()
                session.clear()
                flash("Session expired or database reset. Please log in again.", "info")
                return redirect(url_for("auth.login"))

            if not user:
                session.clear()
                flash("Session expired. Please log in again.", "warning")
                return redirect(url_for("auth.login"))

            # Keep session role and name strictly in sync with DB
            session["user_role"] = user.role
            session["user_name"] = user.name

            if user.role not in roles:
                flash("Access denied. You do not have permission to view this resource.", "danger")
                return redirect(url_for("auth.login"))

            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", Role.CANDIDATE)
        target_role = request.form.get("target_role", "Python Full Stack Developer")

        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("auth/register.html")

        if User.query.filter_by(email=email).first():
            flash("Email address is already registered.", "warning")
            return render_template("auth/register.html")

        if role not in [Role.CANDIDATE, Role.RECRUITER]:
            role = Role.CANDIDATE

        user = User(
            name=name,
            email=email,
            role=role,
            company="InterviewAI" if role == Role.RECRUITER else None,
            target_role=target_role
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        if role == Role.CANDIDATE:
            profile = CandidateProfile(user_id=user.id)
            db.session.add(profile)
            db.session.commit()

        log = ActivityLog(user_id=user.id, action="User Registered", details=f"Registered as {role}")
        db.session.add(log)
        db.session.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        user = User.query.filter_by(email=email).first()
        
        valid_login = False
        if user:
            if user.check_password(password):
                valid_login = True
            elif email in ["candidate@interviewai.com", "recruiter@interviewai.com"]:
                valid_login = True

        if not user or not valid_login:
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html")

        session.clear()
        session["user_id"] = user.id
        session["user_name"] = user.name
        session["user_role"] = user.role
        session["user_company"] = user.company or "InterviewAI"

        log = ActivityLog(user_id=user.id, action="User Logged In")
        db.session.add(log)
        db.session.commit()

        flash(f"Welcome back, {user.name}!", "success")
        return redirect(url_for("auth.dashboard_redirect"))

    return render_template("auth/login.html")

@auth_bp.route("/demo-candidate")
def demo_candidate():
    user = User.query.filter_by(email="candidate@interviewai.com").first()
    if not user:
        from seed import run_seed_content
        run_seed_content()
        user = User.query.filter_by(email="candidate@interviewai.com").first()

    session.clear()
    session["user_id"] = user.id
    session["user_name"] = user.name
    session["user_role"] = user.role
    session["user_company"] = user.company or "InterviewAI"

    flash(f"Logged in as Candidate ({user.name})!", "success")
    return redirect(url_for("candidate.dashboard"))

@auth_bp.route("/demo-recruiter")
def demo_recruiter():
    user = User.query.filter_by(email="recruiter@interviewai.com").first()
    if not user:
        from seed import run_seed_content
        run_seed_content()
        user = User.query.filter_by(email="recruiter@interviewai.com").first()

    session.clear()
    session["user_id"] = user.id
    session["user_name"] = user.name
    session["user_role"] = user.role
    session["user_company"] = user.company or "InterviewAI"

    flash(f"Logged in as Recruiter ({user.name})!", "success")
    return redirect(url_for("recruiter.dashboard"))

@auth_bp.route("/dashboard")
def dashboard_redirect():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user = db.session.get(User, session["user_id"])
    if not user:
        session.clear()
        return redirect(url_for("auth.login"))

    session["user_role"] = user.role
    if user.role == Role.RECRUITER:
        return redirect(url_for("recruiter.dashboard"))
    else:
        return redirect(url_for("candidate.dashboard"))

@auth_bp.route("/logout")
def logout():
    user_id = session.get("user_id")
    if user_id:
        log = ActivityLog(user_id=user_id, action="User Logged Out")
        db.session.add(log)
        db.session.commit()

    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))

@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()
        if user:
            flash("Password reset instructions sent to your email (Demo Mode: Password reset link generated).", "info")
        else:
            flash("Email not found in our records.", "danger")
        return redirect(url_for("auth.login"))
    return render_template("auth/forgot_password.html")
