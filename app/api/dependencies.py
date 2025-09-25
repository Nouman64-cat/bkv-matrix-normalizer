"""FastAPI dependencies for the application."""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import get_settings, Settings

# Optional: Add authentication if needed later
security = HTTPBearer(auto_error=False)


async def get_current_settings() -> Settings:
    """Get current application settings."""
    return get_settings()


async def verify_file_id(file_id: str) -> str:
    """Verify and validate file ID format."""
    if not file_id or len(file_id) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Invalid File ID",
                "message": "File ID must be a valid identifier",
            },
        )
    return file_id


async def optional_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    """
    Optional authentication dependency.
    Can be enabled later if authentication is needed.
    """
    # For now, allow all requests
    return None
