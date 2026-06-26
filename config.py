# Configuration constants
import os
from pathlib import Path
from datetime import timedelta

APP_TITLE = "FINESE • Smart Data Explorer Pro"
APP_ICON = "📊"
LAYOUT = "wide"
INITIAL_SIDEBAR_STATE = "expanded"
TECH_LOGO_URL = "https://cdn-icons-png.flaticon.com/512/2721/2721264.png"
MAX_COLS_FOR_FILTERING = 30
NUMERIC_SLIDER_LIMIT = 8

# Branding constants
BRAND_NAME = "FINESE"
BRAND_COLOR = "#0ea5e9"
BRAND_COLOR_SECONDARY = "#3b82f6"
BRAND_GRADIENT = "linear-gradient(135deg, #0ea5e9, #3b82f6)"

# UI constants
SECTION_HEADER_CLASS = "section-h"
SECTION_SUBHEADER_CLASS = "section-sub"

# Model constants
DEFAULT_LLM_MODEL = "gpt-4o-mini"
MAX_ROWS_FOR_PLOT = 1000

# Model training constants
DEFAULT_CV_FOLDS = 5
DEFAULT_N_ESTIMATORS = 150
DEFAULT_RANDOM_STATE = 42

# Date parsing
DATE_PARSE_THRESHOLD = 0.7

# Export constants
EXPORT_DATE_FORMAT = "%Y%m%d_%H%M"

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
