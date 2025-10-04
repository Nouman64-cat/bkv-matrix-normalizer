"""Data exporter for generating JSON, JSONL, and CSV outputs."""

import csv
import json
import jsonlines
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from io import StringIO
import logging
from datetime import datetime, timezone

from app.core.config import get_settings
from app.core.exceptions import ConversionError

logger = logging.getLogger(__name__)


class JSONGenerator:
    """Generates JSON and JSONL files from processed data."""

    def __init__(self):
        self.settings = get_settings()

    def generate_output(
        self, processed_data: Dict[str, Any], output_format: str = "json"
    ) -> str:
        """
        Generate the requested output string from processed data.

        Args:
            processed_data: Processed data from Excel/CSV processor
            output_format: Output format ('json', 'jsonl', or 'csv')

        Returns:
            Generated content string
        """
        try:
            logger.info(f"Generating {output_format.upper()} from processed data")

            fmt = output_format.lower()
            if fmt == "json":
                return self._generate_json_format(processed_data)
            if fmt == "jsonl":
                return self._generate_jsonl_format(processed_data)
            if fmt == "csv":
                return self._generate_csv_format(processed_data)
            raise ConversionError(f"Unsupported output format: {output_format}")

        except Exception as e:
            logger.error(f"Failed to generate {output_format}: {str(e)}")
            raise ConversionError(
                f"{output_format.upper()} generation failed: {str(e)}"
            )

    def generate_json(
        self, processed_data: Dict[str, Any], output_format: str = "json"
    ) -> str:
        """Backward-compatible wrapper around generate_output."""
        return self.generate_output(processed_data, output_format)

    def _generate_json_format(self, processed_data: Dict[str, Any]) -> str:
        """
        Generate JSON format.

        Args:
            processed_data: Processed data dictionary

        Returns:
            JSON string
        """
        try:
            # Create output structure
            output = {
                "metadata": {
                    "filename": processed_data.get("filename"),
                    "file_type": processed_data.get("file_type"),
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "format": "json",
                }
            }

            # Handle Excel files (multiple sheets)
            if processed_data.get("file_type") == "xlsx":
                output["metadata"]["sheet_count"] = processed_data.get("sheet_count", 0)
                output["metadata"]["total_rows"] = processed_data.get("total_rows", 0)
                output["sheets"] = {}

                sheets_data = processed_data.get("sheets", {})
                for sheet_name, sheet_data in sheets_data.items():
                    output["sheets"][sheet_name] = {
                        "metadata": {
                            "sheet_name": sheet_name,
                            "row_count": sheet_data.get("row_count", 0),
                            "column_count": sheet_data.get("column_count", 0),
                            "headers": sheet_data.get("headers", []),
                        },
                        "data": sheet_data.get("data", []),
                    }

            # Handle CSV/TSV files (single sheet)
            elif processed_data.get("file_type") in {"csv", "tsv"}:
                output["metadata"]["row_count"] = processed_data.get("row_count", 0)
                output["metadata"]["column_count"] = processed_data.get(
                    "column_count", 0
                )
                output["metadata"]["headers"] = processed_data.get("headers", [])
                output["metadata"]["encoding"] = processed_data.get("encoding")
                output["metadata"]["delimiter"] = processed_data.get("delimiter")
                output["data"] = processed_data.get("data", [])

            # Convert to JSON string with proper formatting
            return json.dumps(
                output, indent=2, ensure_ascii=False, default=self._json_serializer
            )

        except Exception as e:
            raise ConversionError(f"JSON formatting failed: {str(e)}")

    def _generate_jsonl_format(self, processed_data: Dict[str, Any]) -> str:
        """
        Generate JSONL format.

        Args:
            processed_data: Processed data dictionary

        Returns:
            JSONL string
        """
        try:
            output_lines = []

            # Add metadata line
            metadata = {
                "type": "metadata",
                "filename": processed_data.get("filename"),
                "file_type": processed_data.get("file_type"),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "format": "jsonl",
            }

            # Handle Excel files (multiple sheets)
            if processed_data.get("file_type") == "xlsx":
                metadata["sheet_count"] = processed_data.get("sheet_count", 0)
                metadata["total_rows"] = processed_data.get("total_rows", 0)
                output_lines.append(
                    json.dumps(
                        metadata, ensure_ascii=False, default=self._json_serializer
                    )
                )

                sheets_data = processed_data.get("sheets", {})
                for sheet_name, sheet_data in sheets_data.items():
                    # Add sheet metadata
                    sheet_metadata = {
                        "type": "sheet_metadata",
                        "sheet_name": sheet_name,
                        "row_count": sheet_data.get("row_count", 0),
                        "column_count": sheet_data.get("column_count", 0),
                        "headers": sheet_data.get("headers", []),
                    }
                    output_lines.append(
                        json.dumps(
                            sheet_metadata,
                            ensure_ascii=False,
                            default=self._json_serializer,
                        )
                    )

                    # Add data rows
                    for row in sheet_data.get("data", []):
                        row_with_meta = {
                            "type": "data",
                            "sheet_name": sheet_name,
                            **row,
                        }
                        output_lines.append(
                            json.dumps(
                                row_with_meta,
                                ensure_ascii=False,
                                default=self._json_serializer,
                            )
                        )

            # Handle CSV/TSV files (single sheet)
            elif processed_data.get("file_type") in {"csv", "tsv"}:
                metadata["row_count"] = processed_data.get("row_count", 0)
                metadata["column_count"] = processed_data.get("column_count", 0)
                metadata["headers"] = processed_data.get("headers", [])
                metadata["encoding"] = processed_data.get("encoding")
                metadata["delimiter"] = processed_data.get("delimiter")
                output_lines.append(
                    json.dumps(
                        metadata, ensure_ascii=False, default=self._json_serializer
                    )
                )

                # Add data rows
                for row in processed_data.get("data", []):
                    row_with_meta = {"type": "data", **row}
                    output_lines.append(
                        json.dumps(
                            row_with_meta,
                            ensure_ascii=False,
                            default=self._json_serializer,
                        )
                    )

            return "\n".join(output_lines)

        except Exception as e:
            raise ConversionError(f"JSONL formatting failed: {str(e)}")

    def _generate_csv_format(self, processed_data: Dict[str, Any]) -> str:
        """Generate CSV format for tabular processed data."""
        records = processed_data.get("data")
        if records is None:
            sheets = processed_data.get("sheets")
            if sheets:
                raise ConversionError("CSV output is not supported for multi-sheet Excel files")
            records = []

        if not isinstance(records, list):
            raise ConversionError("Processed data does not contain tabular records")

        headers = processed_data.get("headers") or sorted({
            key
            for record in records
            if isinstance(record, dict)
            for key in record.keys()
        })

        if not headers:
            headers = ["value"]
            records = [record if isinstance(record, dict) else {"value": record} for record in records]

        buffer = StringIO()
        writer = csv.DictWriter(buffer, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()

        for record in records:
            row = {header: self._format_csv_value(record.get(header)) for header in headers}
            writer.writerow(row)

        return buffer.getvalue()

    def _format_csv_value(self, value: Any) -> Any:
        """Format cell values for CSV export."""
        if value is None:
            return ""
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, (list, dict)):
            return json.dumps(value, ensure_ascii=False)
        return str(value)

    def _json_serializer(self, obj: Any) -> Any:
        """
        Custom JSON serializer for handling special types.

        Args:
            obj: Object to serialize

        Returns:
            Serializable object
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, (set, frozenset)):
            return list(obj)
        elif hasattr(obj, "__dict__"):
            return obj.__dict__
        else:
            return str(obj)

    def generate_file(
        self,
        processed_data: Dict[str, Any],
        output_format: str = "json",
        output_path: Optional[Path] = None,
    ) -> Path:
        """
        Generate an output file and save it to disk.

        Args:
            processed_data: Processed data from Excel/CSV/JSON processors
            output_format: Output format ('json', 'jsonl', or 'csv')
            output_path: Optional output file path

        Returns:
            Path to generated file
        """
        try:
            # Generate content
            content = self.generate_output(processed_data, output_format)

            # Determine output path
            if not output_path:
                filename = processed_data.get("filename", "output")
                base_name = Path(filename).stem
                extension = output_format.lower()
                output_path = (
                    self.settings.upload_path / f"{base_name}_converted.{extension}"
                )

            # Ensure directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            write_kwargs = {"encoding": "utf-8"}
            if output_format.lower() == "csv":
                write_kwargs["newline"] = ""

            with open(output_path, "w", **write_kwargs) as f:
                f.write(content)

            logger.info(f"Generated {output_format.upper()} file: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to generate {output_format} file: {str(e)}")
            raise ConversionError(f"File generation failed: {str(e)}")

    def validate_output_format(self, output_format: str) -> bool:
        """
        Validate if output format is supported.

        Args:
            output_format: Format to validate

        Returns:
            True if format is supported
        """
        return output_format.lower() in self.settings.output_formats_list

    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported output formats.

        Returns:
            List of supported formats
        """
        return self.settings.output_formats_list.copy()

    def get_format_info(self, output_format: str) -> Dict[str, Any]:
        """
        Get information about a specific output format.

        Args:
            output_format: Format to get info for

        Returns:
            Dictionary with format information
        """
        format_info = {
            "json": {
                "name": "JSON",
                "description": "JavaScript Object Notation - structured format with metadata",
                "extension": "json",
                "mime_type": "application/json",
                "features": ["hierarchical", "metadata", "pretty_printed"],
            },
            "jsonl": {
                "name": "JSON Lines",
                "description": "JSON Lines format - one JSON object per line",
                "extension": "jsonl",
                "mime_type": "application/jsonl",
                "features": ["streaming", "line_oriented", "compact"],
            },
        }

        return format_info.get(output_format.lower(), {})


# Global generator instance
json_generator = JSONGenerator()
