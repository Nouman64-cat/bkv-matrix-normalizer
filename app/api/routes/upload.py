"""File upload API endpoints."""

import uuid
import aiofiles
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from fastapi.responses import JSONResponse

from app.core.config import get_settings, Settings
from app.core.exceptions import (
    FileValidationError,
    file_too_large_exception,
    invalid_file_type_exception,
)
from app.models.schemas import UploadResponse, FileInfo, ValidationResponse
from app.validators.file_validator import validate_uploaded_file
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...), settings: Settings = Depends(get_settings)
):
    """
    Upload a file for processing.

    - **file**: Excel (.xlsx), CSV/TSV, or JSON file to upload

    Returns file ID and metadata for further processing.
    """
    try:
        logger.info(f"Received file upload: {file.filename}")

        # Validate file
        await validate_uploaded_file(file)

        # Generate unique file ID
        file_id = str(uuid.uuid4())

        # Get file extension
        file_ext = Path(file.filename).suffix.lower()

        # Create upload path
        upload_path = settings.upload_path / f"{file_id}{file_ext}"

        # Save file
        async with aiofiles.open(upload_path, "wb") as f:
            content = await file.read()
            await f.write(content)

        # Get file size
        file_size = len(content)

        logger.info(f"File saved: {upload_path} (Size: {file_size} bytes)")

        return UploadResponse(
            file_id=file_id,
            filename=file.filename,
            file_type=file_ext.replace(".", ""),
            size=file_size,
            uploaded_at=datetime.now(timezone.utc),
        )

    except FileValidationError as e:
        logger.error(f"File validation failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "File Validation Error",
                "message": e.message,
                "details": e.details,
            },
        )
    except Exception as e:
        logger.error(f"File upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Upload Error", "message": "Failed to upload file"},
        )


@router.get("/{file_id}")
async def get_file_info(file_id: str, settings: Settings = Depends(get_settings)):
    """
    Get information about an uploaded file.

    - **file_id**: Unique file identifier

    Returns file metadata and status.
    """
    try:
        # Find file with any supported extension
        file_path = None
        for ext in settings.allowed_extensions_set:
            potential_path = settings.upload_path / f"{file_id}{ext}"
            if potential_path.exists():
                file_path = potential_path
                break

        if not file_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "File Not Found",
                    "message": f"File with ID '{file_id}' not found",
                },
            )

        # Get file stats
        file_stats = file_path.stat()

        return {
            "file_id": file_id,
            "filename": file_path.name,
            "file_type": file_path.suffix.replace(".", ""),
            "size": file_stats.st_size,
            "created_at": datetime.fromtimestamp(
                file_stats.st_ctime, timezone.utc
            ).isoformat(),
            "modified_at": datetime.fromtimestamp(
                file_stats.st_mtime, timezone.utc
            ).isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get file info for {file_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Server Error",
                "message": "Failed to retrieve file information",
            },
        )


@router.delete("/{file_id}")
async def delete_file(file_id: str, settings: Settings = Depends(get_settings)):
    """
    Delete an uploaded file.

    - **file_id**: Unique file identifier

    Returns confirmation of deletion.
    """
    try:
        # Find and delete file with any supported extension
        deleted = False
        for ext in settings.allowed_extensions_set:
            file_path = settings.upload_path / f"{file_id}{ext}"
            if file_path.exists():
                file_path.unlink()
                deleted = True
                logger.info(f"Deleted file: {file_path}")
                break

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "File Not Found",
                    "message": f"File with ID '{file_id}' not found",
                },
            )

        return {"message": "File deleted successfully", "file_id": file_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete file {file_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Server Error", "message": "Failed to delete file"},
        )
