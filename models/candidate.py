import json
from datetime import datetime
from models.database import db

class CandidateProfile(db.Model):
    __tablename__ = "candidate_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    
    phone = db.Column(db.String(30), nullable=True, default="+1 (555) 234-5678")
    github = db.Column(db.String(255), nullable=True, default="https://github.com/xyz")
    linkedin = db.Column(db.String(255), nullable=True, default="https://linkedin.com/in/xyz")
    portfolio = db.Column(db.String(255), nullable=True, default="https://xyz.dev")
    graduation_year = db.Column(db.String(10), nullable=True, default="2022")

    resume_filename = db.Column(db.String(255), nullable=True)
    resume_path = db.Column(db.String(500), nullable=True)
    resume_score = db.Column(db.Integer, default=0)
    experience_years = db.Column(db.Float, default=0.0)
    education = db.Column(db.String(255), nullable=True, default="Bachelor's in Computer Science")
    summary = db.Column(db.Text, nullable=True)
    
    # Store JSON strings for lists/dicts
    parsed_skills_json = db.Column(db.Text, nullable=True, default="[]")
    missing_skills_json = db.Column(db.Text, nullable=True, default="[]")
    projects_json = db.Column(db.Text, nullable=True, default="[]")
    certificates_json = db.Column(db.Text, nullable=True, default="[]")
    analysis_data_json = db.Column(db.Text, nullable=True, default="{}")
    
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def parsed_skills(self):
        try:
            return json.loads(self.parsed_skills_json or "[]")
        except Exception:
            return []

    @parsed_skills.setter
    def parsed_skills(self, value):
        self.parsed_skills_json = json.dumps(value if isinstance(value, list) else [])

    @property
    def missing_skills(self):
        try:
            return json.loads(self.missing_skills_json or "[]")
        except Exception:
            return []

    @missing_skills.setter
    def missing_skills(self, value):
        self.missing_skills_json = json.dumps(value if isinstance(value, list) else [])

    @property
    def projects(self):
        try:
            return json.loads(self.projects_json or "[]")
        except Exception:
            return []

    @projects.setter
    def projects(self, value):
        self.projects_json = json.dumps(value if isinstance(value, list) else [])

    @property
    def certificates(self):
        try:
            return json.loads(self.certificates_json or "[]")
        except Exception:
            return []

    @certificates.setter
    def certificates(self, value):
        self.certificates_json = json.dumps(value if isinstance(value, list) else [])

    @property
    def analysis_data(self):
        try:
            return json.loads(self.analysis_data_json or "{}")
        except Exception:
            return {}

    @analysis_data.setter
    def analysis_data(self, value):
        self.analysis_data_json = json.dumps(value if isinstance(value, dict) else {})

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user.name if self.user else None,
            "user_email": self.user.email if self.user else None,
            "phone": self.phone,
            "github": self.github,
            "linkedin": self.linkedin,
            "portfolio": self.portfolio,
            "graduation_year": self.graduation_year,
            "resume_filename": self.resume_filename,
            "resume_score": self.resume_score,
            "experience_years": self.experience_years,
            "education": self.education,
            "parsed_skills": self.parsed_skills,
            "missing_skills": self.missing_skills,
            "projects": self.projects,
            "certificates": self.certificates,
            "analysis": self.analysis_data,
            "uploaded_at": self.uploaded_at.strftime("%Y-%m-%d %H:%M:%S") if self.uploaded_at else None
        }
