"""File validation utilities for uploaded files."""

import os
import mimetypes
from pathlib import Path
from typing import Optional, Tuple
from fastapi import UploadFile
import pandas as pd
import openpyxl
from app.core.config import get_settings
from app.core.exceptions import FileValidationError


class FileValidator:
    """Validates uploaded files for processing."""

    def __init__(self):
        self.settings = get_settings()

        # MIME type mappings
        self.mime_types = {
            ".xlsx": [
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "application/vnd.ms-excel",
            ],
            ".csv": ["text/csv", "application/csv", "text/plain"],
        }

    async def validate_file(self, file: UploadFile) -> Tuple[bool, Optional[str]]:
        """
        Validate uploaded file for size, type, and content.

        Args:
            file: FastAPI UploadFile object

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check if file is provided
            if not file:
                return False, "No file provided"

            # Check file size
            if not await self._validate_size(file):
                return (
                    False,
                    f"File size exceeds maximum allowed size of {self.settings.MAX_FILE_SIZE} bytes",
                )

            # Check file extension
            if not self._validate_extension(file.filename):
                return (
                    False,
                    f"File type not allowed. Allowed types: {', '.join(self.settings.allowed_extensions_set)}",
                )

            # Check MIME type
            if not self._validate_mime_type(file):
                return False, "Invalid file format or corrupted file"

            # Validate file content
            if not await self._validate_content(file):
                return False, "File appears to be corrupted or contains invalid data"

            return True, None

        except Exception as e:
            return False, f"Validation error: {str(e)}"

    async def _validate_size(self, file: UploadFile) -> bool:
        """Validate file size."""
        # Read file to check size
        content = await file.read()
        await file.seek(0)  # Reset file pointer

        return len(content) <= self.settings.MAX_FILE_SIZE

    def _validate_extension(self, filename: Optional[str]) -> bool:
        """Validate file extension."""
        if not filename:
            return False

        file_ext = Path(filename).suffix.lower()
        return file_ext in self.settings.allowed_extensions_set

    def _validate_mime_type(self, file: UploadFile) -> bool:
        """Validate MIME type."""
        if not file.filename:
            return False

        file_ext = Path(file.filename).suffix.lower()

        # Check if extension is allowed
        if file_ext not in self.mime_types:
            return False

        # Get expected MIME types for this extension
        expected_types = self.mime_types[file_ext]

        # Check FastAPI detected content type
        if file.content_type in expected_types:
            return True

        # Fallback: check using mimetypes module
        guessed_type, _ = mimetypes.guess_type(file.filename)
        return guessed_type in expected_types

    async def _validate_content(self, file: UploadFile) -> bool:
        """Validate file content by attempting to read it."""
        try:
            if not file.filename:
                return False

            file_ext = Path(file.filename).suffix.lower()
            content = await file.read()
            await file.seek(0)  # Reset file pointer

            if file_ext == ".xlsx":
                return self._validate_excel_content(content)
            elif file_ext == ".csv":
                return self._validate_csv_content(content)

            return False

        except Exception:
            return False

    def _validate_excel_content(self, content: bytes) -> bool:
        """Validate Excel file content."""
        try:
            # Try to load with openpyxl
            from io import BytesIO

            workbook = openpyxl.load_workbook(BytesIO(content))

            # Check if workbook has at least one worksheet
            if not workbook.worksheets:
                return False

            # Try to read at least one cell to ensure it's not completely empty
            worksheet = workbook.active
            has_data = False

            # Check first few rows for any data
            for row in worksheet.iter_rows(max_row=10, max_col=10):
                for cell in row:
                    if cell.value is not None:
                        has_data = True
                        break
                if has_data:
                    break

            workbook.close()
            return has_data

        except Exception:
            return False

    def _validate_csv_content(self, content: bytes) -> bool:
        """Validate CSV file content."""
        try:
            # Try to decode content
            text_content = content.decode("utf-8")

            # Try to read with pandas
            from io import StringIO

            df = pd.read_csv(
                StringIO(text_content), nrows=5
            )  # Read only first 5 rows for validation

            # Check if DataFrame has any data
            return not df.empty and len(df.columns) > 0

        except UnicodeDecodeError:
            # Try different encodings
            try:
                text_content = content.decode("latin-1")
                from io import StringIO

                df = pd.read_csv(StringIO(text_content), nrows=5)
                return not df.empty and len(df.columns) > 0
            except Exception:
                return False
        except Exception:
            return False

    def get_file_info(self, file: UploadFile) -> dict:
        """Get basic file information."""
        return {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": getattr(file, "size", "unknown"),
            "extension": Path(file.filename).suffix.lower() if file.filename else None,
        }


# Global validator instance
file_validator = FileValidator()


async def validate_uploaded_file(file: UploadFile) -> None:
    """
    Validate uploaded file and raise exception if invalid.

    Args:
        file: FastAPI UploadFile object

    Raises:
        FileValidationError: If file validation fails
    """
    is_valid, error_message = await file_validator.validate_file(file)

    if not is_valid:
        raise FileValidationError(
            message=error_message or "File validation failed",
            details=file_validator.get_file_info(file),
        )
