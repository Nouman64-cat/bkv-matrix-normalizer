"""JSON file processor for converting JSON files to structured data."""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import chardet
import pandas as pd

from app.core.config import get_settings
from app.core.exceptions import FileProcessingError

logger = logging.getLogger(__name__)


class JSONProcessor:
    """Processes JSON documents and converts them to tabular data."""

    def __init__(self):
        self.settings = get_settings()

    def process_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Parse a JSON file and extract structured records."""
        try:
            logger.info(f"Processing JSON file: {filename}")

            encoding = self._detect_encoding(file_content)
            logger.debug(f"Detected encoding: {encoding}")

            text_content = file_content.decode(encoding, errors="ignore")
            data = json.loads(text_content)

            records = self._normalize_payload(data)
            headers = sorted({key for record in records for key in record.keys()})

            processed_records = [self._sanitize_record(record, headers) for record in records]

            return {
                "filename": filename,
                "file_type": "json",
                "data": processed_records,
                "headers": headers,
                "row_count": len(processed_records),
                "column_count": len(headers),
                "encoding": encoding,
                "processed_at": datetime.now(timezone.utc).isoformat(),
            }
        except FileProcessingError:
            raise
        except Exception as exc:
            logger.error(f"Failed to process JSON file {filename}: {exc}")
            raise FileProcessingError(f"JSON processing failed: {exc}")

    def get_preview(
        self, file_content: bytes, filename: str, max_rows: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate a preview of the JSON content."""
        max_rows = max_rows or self.settings.MAX_ROWS_PREVIEW

        try:
            parsed = self.process_file(file_content, filename)
            preview_rows = parsed["data"][:max_rows]
            total_rows = parsed["row_count"]

            return {
                "filename": filename,
                "file_type": "json",
                "headers": parsed["headers"],
                "preview_data": preview_rows,
                "total_rows": total_rows,
                "preview_rows": len(preview_rows),
                "encoding": parsed["encoding"],
            }
        except FileProcessingError:
            raise
        except Exception as exc:
            logger.error(f"Failed to generate preview for JSON file {filename}: {exc}")
            raise FileProcessingError(f"JSON preview failed: {exc}")

    def _detect_encoding(self, file_content: bytes) -> str:
        """Detect file encoding with sensible fallbacks."""
        try:
            result = chardet.detect(file_content)
            encoding = result.get("encoding") or "utf-8"

            if result.get("confidence", 0) < 0.7:
                for candidate in ("utf-8", "utf-8-sig", "utf-16", "latin-1"):
                    try:
                        file_content.decode(candidate)
                        return candidate
                    except UnicodeDecodeError:
                        continue
            return encoding
        except Exception:
            return "utf-8"

    def _normalize_payload(self, payload: Any) -> List[Dict[str, Any]]:
        """Normalize arbitrary JSON payloads into record dictionaries."""
        if isinstance(payload, dict):
            for key in ("data", "records", "items", "rows"):
                candidate = payload.get(key)
                if isinstance(candidate, list):
                    payload = candidate
                    break
            else:
                return [self._ensure_mapping(payload)]

        if isinstance(payload, list):
            if not payload:
                return []
            if all(isinstance(item, dict) for item in payload):
                df = pd.json_normalize(payload, sep=".")
                return df.fillna(value=pd.NA).to_dict(orient="records")
            return [self._ensure_mapping({"value": item}) for item in payload]

        return [self._ensure_mapping({"value": payload})]

    def _ensure_mapping(self, value: Any) -> Dict[str, Any]:
        """Ensure the provided value is a dictionary."""
        if isinstance(value, dict):
            return value
        return {"value": value}

    def _sanitize_record(self, record: Dict[str, Any], headers: List[str]) -> Dict[str, Any]:
        """Coerce record values to JSON-serialisable primitives."""
        sanitized: Dict[str, Any] = {}
        for header in headers:
            value = record.get(header)
            sanitized[header] = self._process_value(value)
        return sanitized

    def _process_value(self, value: Any) -> Any:
        """Convert values to JSON/CSV friendly representations."""
        if value is None:
            return None
        try:
            if pd.isna(value):
                return None
        except TypeError:
            pass
        if isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, list):
            return json.dumps(value, ensure_ascii=False)
        if isinstance(value, dict):
            return json.dumps(value, ensure_ascii=False)
        return str(value)


json_processor = JSONProcessor()
