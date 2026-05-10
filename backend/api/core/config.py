from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Application settings
    app_name: str = "FINESE API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # API settings
    api_v1_prefix: str = "/api/v1"
    
    # Database settings
    database_url: Optional[str] = os.getenv("DATABASE_URL", "sqlite:///./finese.db")
    
    # Redis settings for caching
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", 6379))
    redis_db: int = int(os.getenv("REDIS_DB", 0))
    
    # ML settings
    max_rows_for_profiling: int = int(os.getenv("MAX_ROWS_FOR_PROFILING", 10000))
    max_cols_for_profiling: int = int(os.getenv("MAX_COLS_FOR_PROFILING", 50))
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    
    # File upload settings
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", 50 * 1024 * 1024))  # 50MB
    allowed_file_types: list = ["csv", "xlsx", "xls", "json"]

    class Config:
        env_file = ".env"

settings = Settings()