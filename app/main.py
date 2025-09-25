"""Main FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import uvicorn
from pathlib import Path

from app.core.config import get_settings
from app.core.exceptions import BKVMatrixException
from app.api.routes import upload, convert, download
from app.utils.logger import setup_logging


# Initialize settings
settings = get_settings()

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting BKV Matrix Normalizer application")

    # Ensure upload directory exists
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Upload directory ready: {settings.upload_path}")

    yield

    # Shutdown
    logger.info("Shutting down BKV Matrix Normalizer application")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Trusted Host Middleware (security)
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", settings.HOST]
    )

# Static files
static_path = Path("static")
if static_path.exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates_path = Path("templates")
if templates_path.exists():
    templates = Jinja2Templates(directory="templates")


# Exception handlers
@app.exception_handler(BKVMatrixException)
async def bkv_exception_handler(request: Request, exc: BKVMatrixException):
    """Handle custom BKV Matrix exceptions."""
    logger.error(f"BKV Matrix Exception: {exc.message}", extra={"details": exc.details})
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Processing Error",
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": "Invalid request data",
            "details": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
        },
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


# Root endpoint
@app.get("/")
async def root(request: Request):
    """Root endpoint - serves upload page if templates exist, otherwise JSON response."""
    if templates_path.exists():
        return templates.TemplateResponse(
            "upload.html", {"request": request, "title": settings.PROJECT_NAME}
        )
    else:
        return {
            "message": f"Welcome to {settings.PROJECT_NAME}",
            "version": settings.VERSION,
            "docs": "/docs",
            "health": "/health",
        }


# Include API routes
app.include_router(upload.router, prefix=f"{settings.API_V1_STR}/files", tags=["files"])

app.include_router(
    convert.router, prefix=f"{settings.API_V1_STR}/process", tags=["processing"]
)

app.include_router(
    download.router, prefix=f"{settings.API_V1_STR}/download", tags=["download"]
)


# Run application
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.is_development,
        log_level=settings.LOG_LEVEL.lower(),
    )
