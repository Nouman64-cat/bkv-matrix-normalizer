"""Data processing and conversion API endpoints."""

import uuid
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.responses import JSONResponse

from app.core.config import get_settings, Settings
from app.core.exceptions import FileProcessingError, ConversionError
from app.models.schemas import (
    PreviewRequest,
    ConvertRequest,
    ConvertResponse,
    JobStatusResponse,
    ExcelPreviewResponse,
    CSVPreviewResponse,
)
from app.processors.excel_processor import excel_processor
from app.processors.csv_processor import csv_processor
from app.processors.json_generator import json_generator
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

# In-memory job storage (in production, use Redis or database)
jobs: Dict[str, Dict[str, Any]] = {}


@router.get("/preview/{file_id}")
async def preview_file(
    file_id: str,
    max_rows: int = Query(default=100, ge=1, le=1000),
    settings: Settings = Depends(get_settings),
):
    """
    Get a preview of the uploaded file data.

    - **file_id**: Unique file identifier
    - **max_rows**: Maximum number of rows to preview (1-1000)

    Returns preview data with headers and sample rows.
    """
    try:
        logger.info(f"Generating preview for file: {file_id}")

        # Find file
        file_path = None
        file_type = None
        for ext in settings.allowed_extensions_set:
            potential_path = settings.upload_path / f"{file_id}{ext}"
            if potential_path.exists():
                file_path = potential_path
                file_type = ext.replace(".", "")
                break

        if not file_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "File Not Found",
                    "message": f"File with ID '{file_id}' not found",
                },
            )

        # Read file content
        with open(file_path, "rb") as f:
            content = f.read()

        # Process based on file type
        if file_type == "xlsx":
            preview_data = excel_processor.get_preview(
                content, file_path.name, max_rows
            )
        elif file_type == "csv":
            preview_data = csv_processor.get_preview(content, file_path.name, max_rows)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Unsupported File Type",
                    "message": f"File type '{file_type}' is not supported",
                },
            )

        return preview_data

    except HTTPException:
        raise
    except FileProcessingError as e:
        logger.error(f"Preview generation failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "Processing Error",
                "message": e.message,
                "details": e.details,
            },
        )
    except Exception as e:
        logger.error(f"Preview failed for {file_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Server Error", "message": "Failed to generate preview"},
        )


@router.post("/convert/{file_id}", response_model=ConvertResponse)
async def convert_file(
    file_id: str, request: ConvertRequest, settings: Settings = Depends(get_settings)
):
    """
    Convert uploaded file to JSON/JSONL format.

    - **file_id**: Unique file identifier
    - **output_format**: Output format ('json' or 'jsonl')
    - **include_metadata**: Include metadata in output
    - **pretty_print**: Pretty print JSON output

    Returns job ID for tracking conversion progress.
    """
    try:
        logger.info(f"Starting conversion for file: {file_id}")

        # Validate output format
        if not json_generator.validate_output_format(request.output_format):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Invalid Format",
                    "message": f"Unsupported output format: {request.output_format}",
                    "supported_formats": json_generator.get_supported_formats(),
                },
            )

        # Find file
        file_path = None
        file_type = None
        for ext in settings.allowed_extensions_set:
            potential_path = settings.upload_path / f"{file_id}{ext}"
            if potential_path.exists():
                file_path = potential_path
                file_type = ext.replace(".", "")
                break

        if not file_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "File Not Found",
                    "message": f"File with ID '{file_id}' not found",
                },
            )

        # Create conversion job
        job_id = str(uuid.uuid4())
        output_format = getattr(request.output_format, "value", request.output_format)
        jobs[job_id] = {
            "job_id": job_id,
            "file_id": file_id,
            "output_format": output_format,
            "status": "pending",
            "created_at": datetime.now(timezone.utc),
            "file_path": file_path,
            "file_type": file_type,
        }

        # Start conversion in background
        asyncio.create_task(process_conversion(job_id, request))

        return ConvertResponse(
            job_id=job_id,
            file_id=file_id,
            output_format=request.output_format,
            status="pending",
            message="Conversion job started",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start conversion for {file_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Server Error", "message": "Failed to start conversion"},
        )


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get conversion job status.

    - **job_id**: Unique job identifier

    Returns current job status and progress.
    """
    try:
        if job_id not in jobs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Job Not Found",
                    "message": f"Job with ID '{job_id}' not found",
                },
            )

        job = jobs[job_id]

        return JobStatusResponse(
            job_id=job_id,
            status=job["status"],
            message=job.get("message"),
            error=job.get("error"),
            created_at=job["created_at"],
            completed_at=job.get("completed_at"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status for {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Server Error",
                "message": "Failed to retrieve job status",
            },
        )


async def process_conversion(job_id: str, request: ConvertRequest):
    """Background task to process file conversion."""
    try:
        job = jobs[job_id]
        job["status"] = "processing"

        logger.info(f"Processing conversion job: {job_id}")

        # Read file content
        with open(job["file_path"], "rb") as f:
            content = f.read()

        # Process file based on type
        if job["file_type"] == "xlsx":
            processed_data = excel_processor.process_file(
                content, job["file_path"].name
            )
        elif job["file_type"] == "csv":
            processed_data = csv_processor.process_file(content, job["file_path"].name)
        else:
            raise ConversionError(f"Unsupported file type: {job['file_type']}")

        # Generate output
        output_format = job.get("output_format")
        if hasattr(output_format, "value"):
            output_format = output_format.value
            job["output_format"] = output_format
        if not output_format:
            output_format = getattr(request.output_format, "value", request.output_format)
            job["output_format"] = output_format
        output_content = json_generator.generate_json(
            processed_data, output_format
        )

        # Save output file
        output_filename = f"{job['file_id']}_converted.{output_format}"
        output_path = Path("static/uploads") / output_filename

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output_content)

        # Update job status
        job["status"] = "completed"
        job["completed_at"] = datetime.now(timezone.utc)
        job["output_file"] = output_filename
        job["message"] = "Conversion completed successfully"

        logger.info(f"Conversion job completed: {job_id}")

    except Exception as e:
        logger.error(f"Conversion job failed: {job_id} - {str(e)}")
        job["status"] = "failed"
        job["error"] = str(e)
        job["completed_at"] = datetime.now(timezone.utc)
