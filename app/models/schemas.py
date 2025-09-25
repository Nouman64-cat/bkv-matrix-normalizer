"""Pydantic models for request/response schemas."""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class OutputFormat(str, Enum):
    """Supported output formats."""

    JSON = "json"
    JSONL = "jsonl"


class FileType(str, Enum):
    """Supported file types."""

    XLSX = "xlsx"
    CSV = "csv"


class FileInfo(BaseModel):
    """File information model."""

    filename: str
    content_type: str
    size: Optional[int] = None
    extension: Optional[str] = None


class ValidationResponse(BaseModel):
    """File validation response model."""

    is_valid: bool
    message: Optional[str] = None
    file_info: Optional[FileInfo] = None


class UploadResponse(BaseModel):
    """File upload response model."""

    file_id: str
    filename: str
    file_type: FileType
    size: int
    uploaded_at: datetime
    message: str = "File uploaded successfully"


class PreviewRequest(BaseModel):
    """Preview request model."""

    max_rows: Optional[int] = Field(default=100, ge=1, le=1000)


class SheetPreview(BaseModel):
    """Excel sheet preview model."""

    headers: List[str]
    preview_data: List[Dict[str, Any]]
    total_rows: int
    preview_rows: int


class ExcelPreviewResponse(BaseModel):
    """Excel file preview response model."""

    filename: str
    file_type: FileType
    sheets: Dict[str, SheetPreview]
    sheet_count: int


class CSVPreviewResponse(BaseModel):
    """CSV file preview response model."""

    filename: str
    file_type: FileType
    headers: List[str]
    preview_data: List[Dict[str, Any]]
    total_rows: int
    preview_rows: int
    encoding: str
    delimiter: str


class ConvertRequest(BaseModel):
    """Data conversion request model."""

    output_format: OutputFormat = Field(default=OutputFormat.JSON)
    include_metadata: bool = Field(default=True)
    pretty_print: bool = Field(default=True)


class ConversionJob(BaseModel):
    """Conversion job model."""

    job_id: str
    file_id: str
    output_format: OutputFormat
    status: str  # 'pending', 'processing', 'completed', 'failed'
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class ConvertResponse(BaseModel):
    """Data conversion response model."""

    job_id: str
    file_id: str
    output_format: OutputFormat
    status: str
    message: str
    download_url: Optional[str] = None


class JobStatusResponse(BaseModel):
    """Job status response model."""

    job_id: str
    status: str
    progress: Optional[int] = Field(default=None, ge=0, le=100)
    message: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class DownloadResponse(BaseModel):
    """Download response model."""

    filename: str
    content_type: str
    size: int
    download_url: str


class BatchDownloadRequest(BaseModel):
    """Batch download request model."""

    file_ids: List[str] = Field(min_items=1, max_items=10)
    output_format: OutputFormat = Field(default=OutputFormat.JSON)


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    service: str
    version: str
    environment: str


class FileMetadata(BaseModel):
    """File metadata model."""

    filename: str
    file_type: FileType
    size: int
    uploaded_at: datetime
    processed: bool = False
    processed_at: Optional[datetime] = None


class ProcessedData(BaseModel):
    """Processed data model."""

    filename: str
    file_type: FileType
    processed_at: datetime

    class Config:
        # Allow extra fields for flexibility
        extra = "allow"


class ExcelProcessedData(ProcessedData):
    """Excel processed data model."""

    sheets: Dict[str, Dict[str, Any]]
    sheet_count: int
    total_rows: int


class CSVProcessedData(ProcessedData):
    """CSV processed data model."""

    data: List[Dict[str, Any]]
    headers: List[str]
    row_count: int
    column_count: int
    encoding: str
    delimiter: str


# Request/Response model validators
class FileUploadValidator:
    """Validator for file upload requests."""

    @staticmethod
    def validate_file_size(size: int, max_size: int) -> bool:
        """Validate file size."""
        return 0 < size <= max_size

    @staticmethod
    def validate_file_extension(filename: str, allowed_extensions: set) -> bool:
        """Validate file extension."""
        if not filename:
            return False
        extension = filename.lower().split(".")[-1]
        return f".{extension}" in allowed_extensions


class ConversionValidator:
    """Validator for conversion requests."""

    @staticmethod
    def validate_output_format(format_str: str, supported_formats: List[str]) -> bool:
        """Validate output format."""
        return format_str.lower() in [f.lower() for f in supported_formats]
