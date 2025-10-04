"""Application configuration using Pydantic BaseSettings (Pydantic v2).

Notes:
 - List/Set like values provided through environment variables are stored as comma
     separated strings and exposed through convenience properties that parse them.
 - The upload folder is ensured to exist via a field validator (mode="before").
"""

from typing import List, Set, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application Info
    PROJECT_NAME: str = "BKV Matrix Normalizer"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "A FastAPI application for converting Excel/CSV/TSV/JSON to JSON/JSONL/CSV"

    # API Configuration
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "change-me-in-production"

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    # File Upload Settings
    MAX_FILE_SIZE: Optional[int] = None  # Unlimited by default
    UPLOAD_FOLDER: str = "static/uploads"
    ALLOWED_EXTENSIONS: str = ".xlsx,.csv,.tsv,.json"
    OUTPUT_FORMATS: str = "json,jsonl,csv"
    TEMP_FILE_RETENTION: int = 3600  # 1 hour

    # CORS Settings
    CORS_ORIGINS: str = (
        "http://localhost:3000,http://localhost:8000,http://127.0.0.1:8000"
    )

    # Processing Settings
    MAX_ROWS_PREVIEW: int = 100
    CHUNK_SIZE: int = 1000
    PARALLEL_PROCESSING: bool = True

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Security
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    @property
    def allowed_extensions_set(self) -> Set[str]:
        """Get allowed extensions as a set."""
        return {
            ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",") if ext.strip()
        }

    @property
    def output_formats_list(self) -> List[str]:
        """Get output formats as a list."""
        return [fmt.strip() for fmt in self.OUTPUT_FORMATS.split(",") if fmt.strip()]

    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        return [
            origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()
        ]

    @field_validator("UPLOAD_FOLDER", mode="before")
    @classmethod
    def validate_upload_folder(cls, v: str):  # type: ignore[override]
        """Ensure upload folder exists before assigning the value."""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

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

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get settings instance for dependency injection."""
    return settings
