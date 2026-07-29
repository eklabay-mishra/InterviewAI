import pytest
from app import create_app
from models.database import db
from models.user import User, Role

@pytest.fixture
def client():
    app = create_app("development")
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["WTF_CSRF_ENABLED"] = False
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

def test_home_page(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"Interview" in res.data

def test_registration_and_login(client):
    reg_res = client.post("/auth/register", data={
        "name": "Candidate One",
        "email": "cand1@test.com",
        "password": "Password123",
        "role": "candidate",
        "target_role": "Python Developer"
    }, follow_redirects=True)
    assert reg_res.status_code == 200

    login_res = client.post("/auth/login", data={
        "email": "cand1@test.com",
        "password": "Password123"
    }, follow_redirects=True)
    assert login_res.status_code == 200
    assert b"Candidate Dashboard" in login_res.data
