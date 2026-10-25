import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "cybershield-dev-key-change-in-production-2026")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB max upload
    DATABASE = os.getenv("DATABASE_PATH", str(BASE_DIR / "instance" / "cybersecurity.db"))
    UPLOAD_EXTENSIONS = [".csv"]
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True
    DATABASE = ":memory:"
    DEBUG = True

config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig
}
