import json
from datetime import datetime
from models.database import db

class Question(db.Model):
    __tablename__ = "questions"

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False, default="Python")
    difficulty = db.Column(db.String(20), nullable=False, default="Medium")
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(255), nullable=False)
    option_b = db.Column(db.String(255), nullable=False)
    option_c = db.Column(db.String(255), nullable=False)
    option_d = db.Column(db.String(255), nullable=False)
    correct_option = db.Column(db.String(5), nullable=False)  # A, B, C, D
    explanation = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self, include_correct=True):
        data = {
            "id": self.id,
            "category": self.category,
            "difficulty": self.difficulty,
            "question_text": self.question_text,
            "option_a": self.option_a,
            "option_b": self.option_b,
            "option_c": self.option_c,
            "option_d": self.option_d,
            "explanation": self.explanation
        }
        if include_correct:
            data["correct_option"] = self.correct_option
        return data


class McqTest(db.Model):
    __tablename__ = "mcq_tests"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50), nullable=False, default="Python & Web Frameworks")
    total_questions = db.Column(db.Integer, default=20)
    duration_minutes = db.Column(db.Integer, default=15)
    difficulty = db.Column(db.String(20), default="Medium")
    passing_marks = db.Column(db.Integer, default=70)
    attempts_allowed = db.Column(db.Integer, default=3)
    shuffle_questions = db.Column(db.Boolean, default=True)
    negative_marking = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    sessions = db.relationship("TestSession", backref="test", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "total_questions": self.total_questions,
            "duration_minutes": self.duration_minutes,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }


class TestSession(db.Model):
    __tablename__ = "test_sessions"

    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey("mcq_tests.id"), nullable=False)
    score = db.Column(db.Float, default=0.0)
    total_questions = db.Column(db.Integer, default=0)
    correct_answers = db.Column(db.Integer, default=0)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    details_json = db.Column(db.Text, nullable=True, default="[]")

    @property
    def details(self):
        try:
            return json.loads(self.details_json or "[]")
        except Exception:
            return []

    @details.setter
    def details(self, value):
        self.details_json = json.dumps(value if isinstance(value, list) else [])

    def to_dict(self):
        return {
            "id": self.id,
            "candidate_id": self.candidate_id,
            "candidate_name": self.candidate.name if self.candidate else None,
            "test_id": self.test_id,
            "test_title": self.test.title if self.test else None,
            "score": round(self.score, 1),
            "total_questions": self.total_questions,
            "correct_answers": self.correct_answers,
            "details": self.details,
            "completed_at": self.completed_at.strftime("%Y-%m-%d %H:%M:%S") if self.completed_at else None
        }
