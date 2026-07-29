import os
from flask import Flask, render_template, session, redirect, url_for, flash, request
from config import config
from models.database import db
from models.user import User, Role
from models.candidate import CandidateProfile
from models.interview import JobPosting, InterviewSession, InterviewResponse
from models.mcq import Question, McqTest, TestSession
from models.notification import Notification
from models.activity_log import ActivityLog

# Import Blueprints
from routes.auth_routes import auth_bp
from routes.candidate_routes import candidate_bp
from routes.recruiter_routes import recruiter_bp
from routes.api_routes import api_bp

def create_app(config_name="development"):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Ensure Upload folder exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Initialize extensions
    db.init_app(app)

    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            app.logger.warning(f"Database auto-creation warning: {e}")

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(candidate_bp)
    app.register_blueprint(recruiter_bp)
    app.register_blueprint(api_bp)

    # Global Context Processors
    @app.context_processor
    def inject_global_vars():
        unread_count = 0
        user_notifications = []
        current_user = None
        if "user_id" in session:
            try:
                current_user = db.session.get(User, session["user_id"])
                if current_user:
                    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
                    user_notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(5).all()
            except Exception as ex:
                db.session.rollback()
                session.clear()
        return dict(
            current_user=current_user,
            unread_count=unread_count,
            user_notifications=user_notifications
        )

    # Home route
    @app.route("/")
    def index():
        if "user_id" in session:
            return redirect(url_for("auth.dashboard_redirect"))
        return render_template("index.html")

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    from sqlalchemy.exc import ProgrammingError, OperationalError
    @app.errorhandler(ProgrammingError)
    @app.errorhandler(OperationalError)
    def handle_db_errors(e):
        db.session.rollback()
        print(f"[DB Auto-Recover]: {e}")
        with app.app_context():
            try:
                db.create_all()
            except Exception:
                pass
        return redirect(request.referrer or url_for("auth.login"))

    # Auto Create DB tables & Seed default data if empty
    with app.app_context():
        try:
            db.create_all()
            if User.query.count() == 0:
                print("[Auto-Seed] Database empty. Seeding 100 Indian candidates & default accounts...")
                from seed import run_seed_content
                run_seed_content()
        except Exception as e:
            print(f"[Database Auto-Seed Warning]: {e}")

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
