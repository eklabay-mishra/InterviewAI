import json
from datetime import datetime
from models.database import db

class JobPosting(db.Model):
    __tablename__ = "job_postings"

    id = db.Column(db.Integer, primary_key=True)
    recruiter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    role_type = db.Column(db.String(100), nullable=False, default="Python Full Stack Developer")
    skills_required_json = db.Column(db.Text, nullable=False, default="[]")
    description = db.Column(db.Text, nullable=False)
    experience_level = db.Column(db.String(50), default="Mid Level")
    difficulty = db.Column(db.String(30), default="Medium")
    pass_score = db.Column(db.Integer, default=70)
    interview_type = db.Column(db.String(50), default="Technical")
    total_questions = db.Column(db.Integer, default=20)
    time_limit = db.Column(db.Integer, default=45)
    status = db.Column(db.String(20), default="open")  # open, closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    sessions = db.relationship("InterviewSession", backref="job", lazy="dynamic", cascade="all, delete-orphan")

    @property
    def skills_required(self):
        try:
            return json.loads(self.skills_required_json or "[]")
        except Exception:
            return []

    @skills_required.setter
    def skills_required(self, value):
        self.skills_required_json = json.dumps(value if isinstance(value, list) else [])

    def to_dict(self):
        return {
            "id": self.id,
            "recruiter_id": self.recruiter_id,
            "recruiter_name": self.recruiter.name if self.recruiter else None,
            "title": self.title,
            "role_type": self.role_type,
            "skills_required": self.skills_required,
            "description": self.description,
            "experience_level": self.experience_level,
            "difficulty": self.difficulty,
            "pass_score": self.pass_score,
            "status": self.status,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }


class InterviewSession(db.Model):
    __tablename__ = "interview_sessions"

    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey("job_postings.id"), nullable=True)
    role_title = db.Column(db.String(150), nullable=False)
    overall_score = db.Column(db.Float, default=0.0)
    total_questions = db.Column(db.Integer, default=20)
    status = db.Column(db.String(30), default="in_progress")  # in_progress, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    responses = db.relationship("InterviewResponse", backref="session", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "candidate_id": self.candidate_id,
            "candidate_name": self.candidate.name if self.candidate else None,
            "job_id": self.job_id,
            "role_title": self.role_title,
            "overall_score": round(self.overall_score, 1),
            "total_questions": self.total_questions,
            "status": self.status,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "completed_at": self.completed_at.strftime("%Y-%m-%d %H:%M:%S") if self.completed_at else None,
            "responses": [r.to_dict() for r in self.responses.order_by(InterviewResponse.question_number.asc()).all()]
        }


class InterviewResponse(db.Model):
    __tablename__ = "interview_responses"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("interview_sessions.id"), nullable=False)
    question_number = db.Column(db.Integer, nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default="Technical")
    user_answer = db.Column(db.Text, nullable=True)
    score = db.Column(db.Float, default=0.0)
    feedback = db.Column(db.Text, nullable=True)
    model_answer = db.Column(db.Text, nullable=True)
    missing_concepts_json = db.Column(db.Text, nullable=True, default="[]")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def missing_concepts(self):
        try:
            return json.loads(self.missing_concepts_json or "[]")
        except Exception:
            return []

    @missing_concepts.setter
    def missing_concepts(self, value):
        self.missing_concepts_json = json.dumps(value if isinstance(value, list) else [])

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "question_number": self.question_number,
            "question_text": self.question_text,
            "category": self.category,
            "user_answer": self.user_answer,
            "score": round(self.score, 1),
            "feedback": self.feedback,
            "model_answer": self.model_answer,
            "missing_concepts": self.missing_concepts
        }
