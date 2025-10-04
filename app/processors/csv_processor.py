"""Delimited text file processor for converting CSV/TSV files to structured data."""

import pandas as pd
import csv
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from io import StringIO, BytesIO
import logging
from datetime import datetime, timezone
import chardet

from app.core.config import get_settings
from app.core.exceptions import FileProcessingError

logger = logging.getLogger(__name__)


class CSVProcessor:
    """Processes delimited text files (CSV/TSV) and converts them to structured data."""

    def __init__(self):
        self.settings = get_settings()

    def process_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Process delimited text file and extract structured data.

        Args:
            file_content: Raw file content as bytes
            filename: Original filename

        Returns:
            Dictionary containing processed data and metadata
        """
        try:
            file_ext = Path(filename).suffix.lower().lstrip(".") or "csv"
            if file_ext not in {"csv", "tsv"}:
                file_ext = "csv"

            logger.info(f"Processing {file_ext.upper()} file: {filename}")

            # Detect encoding
            encoding = self._detect_encoding(file_content)
            logger.info(f"Detected encoding: {encoding}")

            # Decode content with fallback
            try:
                text_content = file_content.decode(encoding)
            except (LookupError, UnicodeDecodeError):
                text_content = file_content.decode("utf-8", errors="ignore")

            # Detect delimiter
            delimiter = self._detect_delimiter(text_content)
            logger.info(f"Detected delimiter: '{delimiter}'")

            # Read text with pandas
            df = pd.read_csv(
                StringIO(text_content),
                delimiter=delimiter,
                keep_default_na=False,
                na_values=["", "NA", "N/A", "null", "NULL", "None"],
            )

            # Clean column names
            df.columns = [self._clean_column_name(col) for col in df.columns]

            # Process data
            processed_data = []
            for _, row in df.iterrows():
                row_data = {}
                for col in df.columns:
                    value = row[col]
                    row_data[col] = self._process_cell_value(value)
                processed_data.append(row_data)

            # Return structured result
            return {
                "filename": filename,
                "file_type": file_ext,
                "data": processed_data,
                "headers": df.columns.tolist(),
                "row_count": len(processed_data),
                "column_count": len(df.columns),
                "encoding": encoding,
                "delimiter": delimiter,
                "processed_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to process delimited file {filename}: {str(e)}")
            raise FileProcessingError(f"Delimited text processing failed: {str(e)}")

    def _detect_encoding(self, file_content: bytes) -> str:
        """
        Detect file encoding.

        Args:
            file_content: Raw file content as bytes

        Returns:
            Detected encoding
        """
        try:
            # Use chardet to detect encoding
            result = chardet.detect(file_content)
            encoding = result.get("encoding", "utf-8")

            # Fallback to common encodings if detection fails
            if not encoding or result.get("confidence", 0) < 0.7:
                for enc in ["utf-8", "latin-1", "cp1252", "iso-8859-1"]:
                    try:
                        file_content.decode(enc)
                        return enc
                    except UnicodeDecodeError:
                        continue
                return "utf-8"  # Final fallback

            return encoding

        except Exception:
            return "utf-8"

    def _detect_delimiter(self, text_content: str) -> str:
        """
        Detect CSV delimiter.

        Args:
            text_content: Text content of the CSV

        Returns:
            Detected delimiter
        """
        try:
            # Use csv.Sniffer to detect delimiter
            sample = text_content[:2048]  # Use first 2KB for detection
            sniffer = csv.Sniffer()

            # Try to detect delimiter
            try:
                dialect = sniffer.sniff(sample, delimiters=",;\t|")
                return dialect.delimiter
            except csv.Error:
                pass

            # Fallback: count occurrences of common delimiters
            delimiters = [",", ";", "\t", "|"]
            delimiter_counts = {}

            for delimiter in delimiters:
                delimiter_counts[delimiter] = sample.count(delimiter)

            # Return delimiter with highest count
            if delimiter_counts:
                return max(delimiter_counts, key=delimiter_counts.get)

            return ","  # Default fallback

        except Exception:
            return ","

    def _clean_column_name(self, column_name: str) -> str:
        """
        Clean column name by removing unwanted characters and whitespace.

        Args:
            column_name: Original column name

        Returns:
            Cleaned column name
        """
        if pd.isna(column_name):
            return "Unnamed_Column"

        # Convert to string and strip whitespace
        cleaned = str(column_name).strip()

        # Replace empty or whitespace-only names
        if not cleaned:
            return "Unnamed_Column"

        # Remove or replace problematic characters
        cleaned = "".join(
            c if c.isalnum() or c in ["_", "-", " "] else "_" for c in cleaned
        )

        # Replace multiple spaces/underscores with single underscore
        import re

        cleaned = re.sub(r"[\s_]+", "_", cleaned)

        # Remove leading/trailing underscores
        cleaned = cleaned.strip("_")

        return cleaned or "Unnamed_Column"

    def _process_cell_value(self, value: Any) -> Any:
        """
        Process individual cell value and convert to appropriate Python type.

        Args:
            value: Raw cell value from pandas

        Returns:
            Processed cell value
        """
        # Handle pandas NA/NaN values
        if pd.isna(value):
            return None

        # Handle datetime objects
        if isinstance(value, (pd.Timestamp, datetime)):
            return value.isoformat()

        # Handle numeric values
        if isinstance(value, (int, float)):
            if isinstance(value, float) and value.is_integer():
                return int(value)
            return value

        # Handle boolean values
        if isinstance(value, bool):
            return value

        # Handle string values
        if isinstance(value, str):
            cleaned = value.strip()

            # Return None for empty strings
            if not cleaned:
                return None

            # Try to convert to number
            if self._is_number(cleaned):
                try:
                    if "." in cleaned:
                        float_val = float(cleaned)
                        return int(float_val) if float_val.is_integer() else float_val
                    else:
                        return int(cleaned)
                except ValueError:
                    pass

            # Try to convert to boolean
            if cleaned.lower() in ("true", "false", "yes", "no"):
                return cleaned.lower() in ("true", "yes")

            return cleaned

        return str(value) if value is not None else None

    def _is_number(self, value: str) -> bool:
        """Check if a string represents a number."""
        try:
            float(value)
            return True
        except ValueError:
            return False

    def get_preview(
        self, file_content: bytes, filename: str, max_rows: int = None
    ) -> Dict[str, Any]:
        """
        Get a preview of the delimited text file data.

        Args:
            file_content: Raw file content as bytes
            filename: Original filename
            max_rows: Maximum number of rows to preview

        Returns:
            Dictionary containing preview data
        """
        max_rows = max_rows or self.settings.MAX_ROWS_PREVIEW

        try:
            file_ext = Path(filename).suffix.lower().lstrip(".") or "csv"
            if file_ext not in {"csv", "tsv"}:
                file_ext = "csv"

            logger.info(f"Generating preview for {file_ext.upper()} file: {filename}")

            # Detect encoding and delimiter
            encoding = self._detect_encoding(file_content)
            try:
                text_content = file_content.decode(encoding)
            except (LookupError, UnicodeDecodeError):
                text_content = file_content.decode("utf-8", errors="ignore")
            delimiter = self._detect_delimiter(text_content)

            # Read limited rows for preview
            df = pd.read_csv(
                StringIO(text_content),
                delimiter=delimiter,
                nrows=max_rows,
                keep_default_na=False,
                na_values=["", "NA", "N/A", "null", "NULL", "None"],
            )

            # Clean column names
            df.columns = [self._clean_column_name(col) for col in df.columns]

            # Process preview data
            preview_data = []
            for _, row in df.iterrows():
                row_data = {}
                for col in df.columns:
                    value = row[col]
                    row_data[col] = self._process_cell_value(value)
                preview_data.append(row_data)

            # Get total row count
            total_rows = max(sum(1 for _ in StringIO(text_content)) - 1, 0)

            return {
                "filename": filename,
                "file_type": file_ext,
                "headers": df.columns.tolist(),
                "preview_data": preview_data,
                "total_rows": total_rows,
                "preview_rows": len(preview_data),
                "encoding": encoding,
                "delimiter": delimiter,
            }

        except Exception as e:
            logger.error(f"Failed to generate preview for {filename}: {str(e)}")
            raise FileProcessingError(f"Preview generation failed: {str(e)}")


# Global processor instance
csv_processor = CSVProcessor()
