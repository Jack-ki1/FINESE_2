"""
FINESE2 - Configuration Management
Environment-specific configurations for development, testing, and production.
"""
import os
from datetime import timedelta

class Config:
    """Base configuration with common settings."""
    
    # Secret key for session management and JWT
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database configuration
    # Use absolute path for database file
    INSTANCE_PATH = os.path.join(os.getcwd(), 'instance')
    os.makedirs(INSTANCE_PATH, exist_ok=True)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{os.path.join(INSTANCE_PATH, "finese2.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,  # Test connections before using
        'pool_size': 10,
        'max_overflow': 20,
        'pool_recycle': 3600,
    }
    
    # Redis configuration for caching and sessions
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # JWT configuration - set to false by default to disable authentication
    ENABLE_JWT = False  # Disabled by default
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_ALGORITHM = 'HS256'
    
    # File upload configuration
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_UPLOAD_SIZE', 50)) * 1024 * 1024  # Default 50MB
    UPLOAD_FOLDER = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '..',
        'dashboard',
        'uploads'
    )
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'json', 'parquet', 'txt'}
    
    # Rate limiting configuration
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '100 per hour')
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL') or 'memory://'
    RATELIMIT_HEADERS_ENABLED = True
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_TYPE = 'redis'
    SESSION_PERMANENT = True
    
    # AI Provider API Keys (optional)
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
    
    # CORS configuration
    CORS_ORIGINS = os.environ.get('ALLOWED_ORIGINS', '*').split(',')
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Application settings
    DEBUG = False
    TESTING = False
    
    # Data sampling
    DEFAULT_SAMPLE_SIZE = int(os.environ.get('DEFAULT_SAMPLE_SIZE', 10000))
    MAX_ROWS_FOR_ANALYSIS = int(os.environ.get('MAX_ROWS_FOR_ANALYSIS', 100000))
    
    # Model storage
    MODEL_STORAGE_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '..',
        'models'
    )
    
    # Report storage
    REPORT_STORAGE_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '..',
        'reports'
    )

class DevelopmentConfig(Config):
    """Development configuration with debug features enabled."""
    DEBUG = True
    TESTING = False
    
    # More verbose logging in development
    LOG_LEVEL = 'DEBUG'
    
    # Relaxed rate limits for development
    RATELIMIT_DEFAULT = '1000 per hour'
    
    # SQLite is fine for development
    INSTANCE_PATH = os.path.join(os.getcwd(), 'instance')
    os.makedirs(INSTANCE_PATH, exist_ok=True)
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(INSTANCE_PATH, "finese2_dev.db")}'
    
    # Enable SQLAlchemy echo for debugging queries
    SQLALCHEMY_ECHO = True
    
    # Development environment
    ENVIRONMENT = 'development'
    
    # Don't require Redis in development
    REDIS_AVAILABLE = False
    
    # Disable JWT by default in development
    ENABLE_JWT = False

class ProductionConfig(Config):
    """Production configuration with security and performance optimizations."""
    DEBUG = False
    TESTING = False
    
    # JWT can be enabled by setting ENABLE_JWT=true environment variable
    ENABLE_JWT = os.environ.get('ENABLE_JWT', 'False').lower() == 'true'
    
    # Enforce secure settings in production (validated at runtime in __init__)
    def __init__(self):
        super().__init__()
        if not os.environ.get('SECRET_KEY'):
            raise RuntimeError("SECRET_KEY environment variable must be set in production")
    
    # Stricter rate limiting in production
    RATELIMIT_DEFAULT = '50 per hour'
    
    # More restrictive upload size in production
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_UPLOAD_SIZE', 25)) * 1024 * 1024  # 25MB
    
    # Secure cookie settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # JWT security
    JWT_COOKIE_SECURE = True
    JWT_ACCESS_COOKIE_PATH = '/api/'
    JWT_REFRESH_COOKIE_PATH = '/api/auth/refresh'
    
    # Logging
    LOG_LEVEL = 'WARNING'
    
    # Disable SQLAlchemy echo in production
    SQLALCHEMY_ECHO = False
    
    # Production environment
    ENVIRONMENT = 'production'
    
    # Ensure Redis is required in production
    REDIS_AVAILABLE = True

class TestingConfig(Config):
    """Testing configuration with in-memory database and disabled features."""
    TESTING = True
    DEBUG = True
    
    # Use in-memory SQLite for fast tests
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ECHO = False
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False
    
    # No rate limiting in tests
    RATELIMIT_ENABLED = False
    
    # Minimal logging in tests
    LOG_LEVEL = 'ERROR'
    
    # Fast token expiration for tests
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(hours=1)
    
    # Testing environment
    ENVIRONMENT = 'testing'
    
    # Redis availability for testing
    REDIS_AVAILABLE = False

# Configuration mapping for easy selection
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}

def get_config(env=None):
    """
    Get configuration class based on environment.
    
    Args:
        env: Environment name (development, production, testing)
    
    Returns:
        Configuration class
    """
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development')
    
    return config_map.get(env, config_map['default'])
