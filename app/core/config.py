"""Application configuration using Pydantic BaseSettings."""

from typing import List, Set
from pydantic import BaseSettings, validator
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application Info
    PROJECT_NAME: str = "BKV Matrix Normalizer"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "A FastAPI application for converting Excel/CSV to JSON/JSONL"

    # API Configuration
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "change-me-in-production"

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    # File Upload Settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_FOLDER: str = "static/uploads"
    ALLOWED_EXTENSIONS: Set[str] = {".xlsx", ".csv"}
    OUTPUT_FORMATS: List[str] = ["json", "jsonl"]
    TEMP_FILE_RETENTION: int = 3600  # 1 hour

    # CORS Settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    # Processing Settings
    MAX_ROWS_PREVIEW: int = 100
    CHUNK_SIZE: int = 1000
    PARALLEL_PROCESSING: bool = True

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Security
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    @validator("ALLOWED_EXTENSIONS", pre=True)
    def parse_extensions(cls, v):
        """Parse comma-separated extensions from environment variable."""
        if isinstance(v, str):
            return {ext.strip() for ext in v.split(",") if ext.strip()}
        return v

    @validator("OUTPUT_FORMATS", pre=True)
    def parse_formats(cls, v):
        """Parse comma-separated formats from environment variable."""
        if isinstance(v, str):
            return [fmt.strip() for fmt in v.split(",") if fmt.strip()]
        return v

    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        """Parse comma-separated CORS origins from environment variable."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @validator("UPLOAD_FOLDER")
    def create_upload_folder(cls, v):
        """Ensure upload folder exists."""
        upload_path = Path(v)
        upload_path.mkdir(parents=True, exist_ok=True)
        return str(upload_path)

    @property
    def upload_path(self) -> Path:
        """Get upload folder as Path object."""
        return Path(self.UPLOAD_FOLDER)

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT.lower() == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT.lower() == "production"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get settings instance for dependency injection."""
    return settings
