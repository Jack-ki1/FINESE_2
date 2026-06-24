"""
FINESE2 - Flask Extensions Initialization
Centralized extension initialization for the application factory pattern.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS

# Initialize extensions (not bound to app yet - will be done in init_extensions)
db = SQLAlchemy()

# Pre-create SQLite directory if using the default sqlite:///instance/... path.
# This prevents "unable to open database file" on fresh checkouts.
try:
    import os
    from app.config import get_config
    cfg = get_config(os.environ.get('FLASK_ENV', 'development'))
    uri = getattr(cfg, 'SQLALCHEMY_DATABASE_URI', '') or ''
    if uri.startswith('sqlite:///'):
        db_path = uri.split('sqlite:///', 1)[1]
        db_dir = os.path.dirname(os.path.abspath(db_path))
        os.makedirs(db_dir, exist_ok=True)
except Exception:
    pass

migrate = Migrate()
limiter = Limiter(key_func=get_remote_address)


def init_extensions(app):
    """
    Initialize and bind all Flask extensions to the application.
    
    Args:
        app: Flask application instance
    """
    # Database (SQLAlchemy ORM)
    db.init_app(app)
    
    # Database migrations (Alembic)
    migrate.init_app(app, db)
    
    # Rate limiting - use memory store by default
    app.config.setdefault('RATELIMIT_STORAGE_URL', 'memory://')
    limiter.init_app(app)
    
    # CORS (Cross-Origin Resource Sharing)
    allowed_origins = app.config.get('CORS_ORIGINS', ['*'])
    CORS(
        app,
        origins=allowed_origins,
        supports_credentials=True,
        allow_headers=['Content-Type', 'Authorization'],
        methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    )