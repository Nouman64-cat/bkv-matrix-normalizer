"""Application logging configuration.

Provides console + rotating file handlers. If LOG_FORMAT=json is configured but
the optional dependency python-json-logger is missing, it falls back to the
standard formatter instead of crashing application startup.
"""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Dict, Any

from app.core.config import get_settings

try:
    # Probe optional json logger dependency early so we can gracefully fallback
    import pythonjsonlogger  # type: ignore  # noqa: F401

    HAVE_JSON_LOGGER = True
except Exception:  # pragma: no cover - defensive
    HAVE_JSON_LOGGER = False


def setup_logging() -> None:
    """Setup application logging configuration."""
    settings = get_settings()

    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    use_json = settings.LOG_FORMAT.lower() == "json" and HAVE_JSON_LOGGER

    # Logging configuration
    config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            # Only include json formatter if dependency present
            **(
                {
                    "json": {
                        "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                        "format": "%(asctime)s %(name)s %(levelname)s %(filename)s %(lineno)d %(funcName)s %(message)s",
                    }
                }
                if HAVE_JSON_LOGGER
                else {}
            ),
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "json" if use_json else "default",
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json" if use_json else "detailed",
                "filename": str(logs_dir / "app.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8",
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "json" if use_json else "detailed",
                "filename": str(logs_dir / "error.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "app": {
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "file", "error_file"],
                "propagate": False,
            },
            "uvicorn": {"level": "INFO", "handlers": ["console"], "propagate": False},
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console", "error_file"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
        },
        "root": {"level": settings.LOG_LEVEL, "handlers": ["console"]},
    }

    # Apply configuration with fallback if json formatter still misconfigured
    try:
        logging.config.dictConfig(config)
    except Exception:
        # Fallback: force plain text formatters
        for handler in ("console", "file", "error_file"):
            if handler in config["handlers"]:
                config["handlers"][handler]["formatter"] = (
                    "detailed" if handler != "console" else "default"
                )
        config["formatters"].pop("json", None)
        logging.config.dictConfig(config)

    if settings.LOG_FORMAT.lower() == "json" and not HAVE_JSON_LOGGER:
        logging.getLogger("app").warning(
            "LOG_FORMAT=json requested but python-json-logger not installed. Using text format."
        )

    # Set logging level for third-party libraries
    logging.getLogger("pandas").setLevel(logging.WARNING)
    logging.getLogger("openpyxl").setLevel(logging.WARNING)
    logging.getLogger("chardet").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(f"app.{name}")
