"""File download API endpoints."""

from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import FileResponse, JSONResponse

from app.core.config import get_settings, Settings
from app.models.schemas import DownloadResponse, BatchDownloadRequest
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/{file_id}")
async def download_converted_file(
    file_id: str, settings: Settings = Depends(get_settings)
):
    """
    Download converted file.

    - **file_id**: Unique file identifier

    Returns the converted file for download.
    """
    try:
        logger.info(f"Download request for file: {file_id}")

        # Look for converted files
        download_path = None
        for format_ext in ["json", "jsonl"]:
            potential_path = settings.upload_path / f"{file_id}_converted.{format_ext}"
            if potential_path.exists():
                download_path = potential_path
                break

        if not download_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "File Not Found",
                    "message": f"Converted file with ID '{file_id}' not found",
                },
            )

        # Determine content type
        content_type = (
            "application/json"
            if download_path.suffix == ".json"
            else "application/jsonl"
        )

        return FileResponse(
            path=download_path, filename=download_path.name, media_type=content_type
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download failed for {file_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Server Error", "message": "Failed to download file"},
        )


@router.get("/info/{file_id}")
async def get_download_info(file_id: str, settings: Settings = Depends(get_settings)):
    """
    Get download information for a converted file.

    - **file_id**: Unique file identifier

    Returns file information and download URL.
    """
    try:
        # Look for converted files
        download_path = None
        for format_ext in ["json", "jsonl"]:
            potential_path = settings.upload_path / f"{file_id}_converted.{format_ext}"
            if potential_path.exists():
                download_path = potential_path
                break

        if not download_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "File Not Found",
                    "message": f"Converted file with ID '{file_id}' not found",
                },
            )

        # Get file stats
        file_stats = download_path.stat()
        content_type = (
            "application/json"
            if download_path.suffix == ".json"
            else "application/jsonl"
        )

        return {
            "filename": download_path.name,
            "content_type": content_type,
            "size": file_stats.st_size,
            "download_url": f"/api/v1/download/{file_id}",
            "created_at": file_stats.st_ctime,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get download info for {file_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Server Error",
                "message": "Failed to retrieve download information",
            },
        )
