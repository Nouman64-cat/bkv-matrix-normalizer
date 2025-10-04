"""File validation utilities for uploaded files."""

import os
import mimetypes
import csv
import json
from io import StringIO
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
            ".tsv": ["text/tab-separated-values", "application/tab-separated-values", "text/plain"],
            ".json": ["application/json", "text/json", "application/octet-stream"],
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
                max_size = self.settings.MAX_FILE_SIZE
                limit_text = (
                    f"{max_size:,} bytes" if isinstance(max_size, int) and max_size > 0 else "configured limit"
                )
                return (
                    False,
                    f"File size exceeds maximum allowed size of {limit_text}",
                )

            # Check file extension
            if not self._validate_extension(file.filename):
                return (
                    False,
                    f"File type not allowed. Allowed types: {', '.join(sorted(self.settings.allowed_extensions_set))}",
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
        content = await file.read()
        await file.seek(0)  # Reset file pointer

        max_size = self.settings.MAX_FILE_SIZE
        if max_size is None or max_size <= 0:
            return True

        return len(content) <= max_size

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
            if file_ext in {".csv", ".tsv"}:
                return self._validate_tabular_content(content)
            if file_ext == ".json":
                return self._validate_json_content(content)

            return False

        except Exception:
            return False

    def _decode_text_content(self, content: bytes) -> str:
        """Decode text content with fallback encodings."""
        for encoding in ("utf-8", "utf-8-sig", "utf-16", "utf-16le", "utf-16be", "latin-1"):
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue
        return content.decode("utf-8", errors="ignore")

    def _detect_delimiter(self, text_content: str) -> str:
        """Detect delimiter in delimited text content."""
        sample = text_content[:2048]
        try:
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample, delimiters=",;	|")
            return dialect.delimiter
        except csv.Error:
            counts = {d: sample.count(d) for d in [",", "	", ";", "|"]}
            if counts:
                return max(counts, key=counts.get)
            return ","

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

    def _validate_json_content(self, content: bytes) -> bool:
        """Validate JSON file content."""
        try:
            text_content = self._decode_text_content(content)
            data = json.loads(text_content)
            return isinstance(data, (dict, list))
        except Exception:
            return False

    def _validate_tabular_content(self, content: bytes) -> bool:
        """Validate delimited text file content."""
        try:
            text_content = self._decode_text_content(content)
            delimiter = self._detect_delimiter(text_content)

            df = pd.read_csv(
                StringIO(text_content),
                delimiter=delimiter,
                nrows=5,
                keep_default_na=False,
                na_values=["", "NA", "N/A", "null", "NULL", "None"],
            )

            return not df.empty and len(df.columns) > 0

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
