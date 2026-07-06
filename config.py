# Configuration constants
import os
from pathlib import Path
from datetime import timedelta


# Concurrency / parallelism guard
N_JOBS = 1 if os.environ.get("SPACE_ID") else -1


class Config:
    """Flask application configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY", os.urandom(32))
    UPLOAD_FOLDER = Path("static/uploads")
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024   # 50 MB upload limit
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///finese.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
    
    # Session configuration
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = Path('flask_session')
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)

    # Computed guards
    @property
    def ai_enabled(self):
        return bool(self.ANTHROPIC_API_KEY)
