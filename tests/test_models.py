import pytest
from app import create_app
from models.database import db
from models.user import User, Role
from models.candidate import CandidateProfile

@pytest.fixture
def app_instance():
    app = create_app("development")
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

def test_user_password_hashing(app_instance):
    user = User(name="Eklabay Mishra", email="eklabay@interviewai.com", role=Role.RECRUITER, company="InterviewAI")
    user.set_password("RecruiterPass123")
    assert user.check_password("RecruiterPass123") is True
    assert user.check_password("WrongPassword") is False
    assert user.role == Role.RECRUITER
    assert user.company == "InterviewAI"

def test_candidate_profile_json_properties(app_instance):
    user = User(name="Alex Rivera", email="alex@test.com", role=Role.CANDIDATE)
    user.set_password("pass")
    db.session.add(user)
    db.session.commit()

    profile = CandidateProfile(user_id=user.id)
    profile.parsed_skills = ["Python", "Flask", "MySQL"]
    profile.missing_skills = ["Docker"]
    profile.projects = [{"title": "AI Evaluator", "tech": "Python, Flask"}]
    profile.certificates = ["AWS Certified"]
    db.session.add(profile)
    db.session.commit()

    fetched = CandidateProfile.query.filter_by(user_id=user.id).first()
    assert "Python" in fetched.parsed_skills
    assert "Docker" in fetched.missing_skills
    assert fetched.projects[0]["title"] == "AI Evaluator"
    assert fetched.certificates[0] == "AWS Certified"
