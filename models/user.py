from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from models.database import db

class Role:
    CANDIDATE = "candidate"
    RECRUITER = "recruiter"

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=Role.CANDIDATE)
    status = db.Column(db.String(20), nullable=False, default="active")  # active, suspended
    company = db.Column(db.String(100), nullable=True, default="InterviewAI")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    avatar = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    target_role = db.Column(db.String(100), nullable=True, default="Python Full Stack Developer")

    # Relationships
    candidate_profile = db.relationship("CandidateProfile", backref="user", uselist=False, cascade="all, delete-orphan")
    job_postings = db.relationship("JobPosting", backref="recruiter", lazy="dynamic", foreign_keys="JobPosting.recruiter_id")
    interview_sessions = db.relationship("InterviewSession", backref="candidate", lazy="dynamic", foreign_keys="InterviewSession.candidate_id")
    test_sessions = db.relationship("TestSession", backref="candidate", lazy="dynamic", foreign_keys="TestSession.candidate_id")
    notifications = db.relationship("Notification", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    activity_logs = db.relationship("ActivityLog", backref="user", lazy="dynamic", cascade="all, delete-orphan")

    @property
    def last_interview_session(self):
        from models.interview import InterviewSession
        return self.interview_sessions.order_by(InterviewSession.created_at.desc()).first()

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "company": self.company,
            "status": self.status,
            "target_role": self.target_role,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
