import os
import socket
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

def is_mysql_available(host="localhost", port=3306):
    """Check if MySQL daemon is accepting socket connections on port 3306."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        result = sock.connect_ex((host, int(port)))
        sock.close()
        return result == 0
    except Exception:
        return False

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "interview_ai_super_secret_enterprise_key_2026_x89a")
    
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
    MYSQL_DB = os.getenv("MYSQL_DB", "interview_ai")
    
    DEFAULT_MYSQL_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    FALLBACK_SQLITE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'interview_ai.db')}"
    
    # Intelligently select MySQL if daemon is active or DATABASE_URL is set, else SQLite
    if os.getenv("DATABASE_URL"):
        SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    elif is_mysql_available(MYSQL_HOST, MYSQL_PORT):
        SQLALCHEMY_DATABASE_URI = DEFAULT_MYSQL_URI
    else:
        SQLALCHEMY_DATABASE_URI = FALLBACK_SQLITE_URI

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 280,
        "pool_pre_ping": True
    }
    
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads", "resumes")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB limit
    ALLOWED_EXTENSIONS = {"pdf", "docx"}
    
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    
    SESSION_TYPE = "filesystem"
    SESSION_PERMANENT = False

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig
}
