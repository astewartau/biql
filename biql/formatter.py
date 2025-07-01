"""
Output formatters for BIDS Query Language (BIQL)

Formats query results in different output formats.
"""

import csv
import io
import json
from typing import Any, Dict, List, Optional


class BIQLFormatter:
    """Formats query results in different output formats"""

    @staticmethod
    def format(
        results: List[Dict],
        format_type: str = "json",
        original_files: Optional[List] = None,
    ) -> str:
        """Format results based on specified type"""
        format_type = format_type.lower() if format_type else "json"

        if format_type == "json":
            return BIQLFormatter._format_json(results)
        elif format_type == "table":
            return BIQLFormatter._format_table(results)
        elif format_type == "csv":
            return BIQLFormatter._format_csv(results)
        elif format_type == "paths":
            return BIQLFormatter._format_paths(results, original_files)
        elif format_type == "tsv":
            return BIQLFormatter._format_tsv(results)
        else:
            # Default to JSON for unknown formats
            return BIQLFormatter._format_json(results)

    @staticmethod
    def _format_json(results: List[Dict]) -> str:
        """Format results as JSON"""

        def json_serializer(obj):
            """Custom JSON serializer for complex objects"""
            if hasattr(obj, "__dict__"):
                return obj.__dict__
            return str(obj)

        return json.dumps(
            results, indent=2, default=json_serializer, ensure_ascii=False
        )

    @staticmethod
    def _format_table(results: List[Dict]) -> str:
        """Format results as ASCII table"""
        if not results:
            return "No results found."

        # Get all unique keys, excluding internal fields
        all_keys = set()
        for result in results:
            for key in result.keys():
                if not key.startswith("_") or key == "_count":
                    all_keys.add(key)
        all_keys = sorted(all_keys)

        if not all_keys:
            return "No data to display."

        # Calculate column widths
        widths = {}
        for key in all_keys:
            widths[key] = len(key)

        for result in results:
            for key in all_keys:
                value = BIQLFormatter._format_value_for_display(result.get(key))
                widths[key] = max(widths[key], len(value))

        # Build table
        lines = []

        # Header
        header = "|"
        for key in all_keys:
            header += f" {key:<{widths[key]}} |"
        lines.append(header)

        # Separator
        separator = "|"
        for key in all_keys:
            separator += f" {'-' * widths[key]} |"
        lines.append(separator)

        # Data rows
        for result in results:
            row = "|"
            for key in all_keys:
                value = BIQLFormatter._format_value_for_display(result.get(key))
                row += f" {value:<{widths[key]}} |"
            lines.append(row)

        return "\n".join(lines)

    @staticmethod
    def _format_csv(results: List[Dict]) -> str:
        """Format results as CSV"""
        if not results:
            return ""

        output = io.StringIO()

        # Get all fieldnames, excluding internal fields
        fieldnames = set()
        for result in results:
            for key in result.keys():
                if not key.startswith("_") or key == "_count":
                    fieldnames.add(key)
        fieldnames = sorted(fieldnames)

        if fieldnames:
            writer = csv.DictWriter(
                output, fieldnames=fieldnames, extrasaction="ignore"
            )
            writer.writeheader()

            for result in results:
                # Convert complex values for CSV output
                csv_row = {}
                for key in fieldnames:
                    value = result.get(key)
                    csv_row[key] = BIQLFormatter._format_value_for_csv(value)
                writer.writerow(csv_row)

        return output.getvalue()

    @staticmethod
    def _format_tsv(results: List[Dict]) -> str:
        """Format results as TSV (Tab-Separated Values)"""
        if not results:
            return ""

        # Get all fieldnames, excluding internal fields
        fieldnames = set()
        for result in results:
            for key in result.keys():
                if not key.startswith("_") or key == "_count":
                    fieldnames.add(key)
        fieldnames = sorted(fieldnames)

        if not fieldnames:
            return ""

        lines = []

        # Header
        lines.append("\t".join(fieldnames))

        # Data rows
        for result in results:
            row_values = []
            for key in fieldnames:
                value = result.get(key)
                formatted_value = BIQLFormatter._format_value_for_csv(value)
                row_values.append(formatted_value)
            lines.append("\t".join(row_values))

        return "\n".join(lines)

    @staticmethod
    def _format_paths(
        results: List[Dict], original_files: Optional[List] = None
    ) -> str:
        """Format results as file paths only - always shows actual file paths regardless of SELECT clause"""
        paths = []

        # If we have original files, use them directly
        if original_files:
            for file in original_files:
                if hasattr(file, "filepath"):
                    paths.append(str(file.filepath))
                elif hasattr(file, "relative_path"):
                    paths.append(str(file.relative_path))
        else:
            # Fallback to extracting paths from results
            for result in results:
                if "filepath" in result:
                    if isinstance(result["filepath"], list):
                        paths.extend(str(path) for path in result["filepath"])
                    else:
                        paths.append(str(result["filepath"]))
                elif "relative_path" in result:
                    if isinstance(result["relative_path"], list):
                        paths.extend(str(path) for path in result["relative_path"])
                    else:
                        paths.append(str(result["relative_path"]))
                elif "filename" in result:
                    if isinstance(result["filename"], list):
                        paths.extend(str(filename) for filename in result["filename"])
                    else:
                        paths.append(str(result["filename"]))

        # Sort paths for consistent output
        return "\n".join(sorted(paths))

    @staticmethod
    def _format_value_for_display(value: Any) -> str:
        """Format a value for display in tables"""
        if value is None:
            return ""
        elif isinstance(value, dict):
            # For metadata objects, show key count
            return f"{{...{len(value)} keys...}}"
        elif isinstance(value, list):
            # For lists, show item count
            return f"[...{len(value)} items...]"
        elif isinstance(value, (int, float)):
            return str(value)
        else:
            return str(value)

    @staticmethod
    def _format_value_for_csv(value: Any) -> str:
        """Format a value for CSV output"""
        if value is None:
            return ""
        elif isinstance(value, dict):
            # Convert dict to JSON string for CSV
            return json.dumps(value, separators=(",", ":"))
        elif isinstance(value, list):
            # Convert list to JSON string for CSV
            return json.dumps(value, separators=(",", ":"))
        elif isinstance(value, bool):
            return "true" if value else "false"
        else:
            return str(value)
