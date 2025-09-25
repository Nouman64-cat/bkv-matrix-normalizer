"""Custom exception classes for the application."""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class BKVMatrixException(Exception):
    """Base exception class for BKV Matrix Normalizer."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class FileValidationError(BKVMatrixException):
    """Raised when file validation fails."""

    pass


class FileProcessingError(BKVMatrixException):
    """Raised when file processing fails."""

    pass


class ConversionError(BKVMatrixException):
    """Raised when data conversion fails."""

    pass


class FileNotFoundError(BKVMatrixException):
    """Raised when a requested file is not found."""

    pass


# HTTP Exception helpers
def create_http_exception(
    status_code: int, message: str, details: Optional[Dict[str, Any]] = None
) -> HTTPException:
    """Create a formatted HTTP exception."""
    return HTTPException(
        status_code=status_code, detail={"message": message, "details": details or {}}
    )


def file_not_found_exception(file_id: str) -> HTTPException:
    """Standard file not found exception."""
    return create_http_exception(
        status_code=status.HTTP_404_NOT_FOUND,
        message=f"File with ID '{file_id}' not found",
        details={"file_id": file_id},
    )


def file_too_large_exception(max_size: int) -> HTTPException:
    """File too large exception."""
    return create_http_exception(
        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        message=f"File size exceeds maximum allowed size of {max_size} bytes",
        details={"max_size": max_size},
    )


def invalid_file_type_exception(allowed_types: list) -> HTTPException:
    """Invalid file type exception."""
    return create_http_exception(
        status_code=status.HTTP_400_BAD_REQUEST,
        message="Invalid file type",
        details={"allowed_types": allowed_types},
    )


def processing_error_exception(error_msg: str) -> HTTPException:
    """File processing error exception."""
    return create_http_exception(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="File processing failed",
        details={"error": error_msg},
    )
