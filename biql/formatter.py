"""
Output formatters for BIDS Query Language (BIQL)

Formats query results in different output formats.
"""

import csv
import io
import json
import os
import shutil
from typing import Any, Dict, List, Optional

from tabulate import tabulate


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
        """Format results as ASCII table using tabulate with console width awareness"""
        if not results:
            return "No results found."

        # Get all unique keys, preserving order from first result
        all_keys = []
        seen_keys = set()
        for result in results:
            for key in result.keys():
                if (
                    not key.startswith("_") or key == "_count"
                ) and key not in seen_keys:
                    all_keys.append(key)
                    seen_keys.add(key)

        if not all_keys:
            return "No data to display."

        # Get console width
        try:
            console_width = shutil.get_terminal_size().columns
        except (AttributeError, OSError):
            console_width = 80  # Default fallback

        # Calculate actual content widths for each column
        col_widths = {}
        for key in all_keys:
            # Start with header width
            col_widths[key] = len(key)
            # Check content width
            for result in results:
                value = BIQLFormatter._format_value_for_display(result.get(key))
                col_widths[key] = max(col_widths[key], len(str(value)))

        # Define sensible max widths for known columns (only used when space is limited)
        max_width_config = {
            "filepath": 50,
            "relative_path": 50,
            "filename": 35,
            "metadata": 30,
        }

        # Calculate total width needed if we show all columns without limits
        total_needed_width = 0
        for i, key in enumerate(all_keys):
            actual_width = col_widths[key]
            separator_width = 3 if i > 0 else 0  # " | "
            total_needed_width += actual_width + separator_width

        margin = 10
        available_width = console_width - margin

        # If all columns fit comfortably, show them all without maxcolwidths restrictions
        if total_needed_width <= available_width:
            selected_keys = all_keys
            maxcolwidths = None  # No restrictions needed
        else:
            # We need to be selective - preserve order but apply width limits
            selected_keys = []
            maxcolwidths = []
            estimated_width = 0

            # First pass: try to fit all columns with reasonable width limits
            for key in all_keys:
                max_width = max_width_config.get(key, 30)  # Default reasonable limit
                actual_width = min(col_widths[key], max_width)
                separator_width = 3 if selected_keys else 0
                needed_width = actual_width + separator_width

                if estimated_width + needed_width <= available_width:
                    selected_keys.append(key)
                    maxcolwidths.append(max_width)
                    estimated_width += needed_width
                else:
                    break

            # If we couldn't fit all columns, ensure we have at least some
            if not selected_keys and all_keys:
                # Show first column with remaining space
                selected_keys = [all_keys[0]]
                maxcolwidths = [available_width - 5]

        # Prepare data for tabulate
        table_data = []
        for result in results:
            row = []
            for key in selected_keys:
                value = BIQLFormatter._format_value_for_display(result.get(key))
                row.append(value)
            table_data.append(row)

        # Use tabulate with maxcolwidths for automatic text wrapping (only when needed)
        if maxcolwidths is not None:
            formatted_table = tabulate(
                table_data,
                headers=selected_keys,
                tablefmt="simple",
                stralign="left",
                numalign="left",
                maxcolwidths=maxcolwidths,
            )
        else:
            formatted_table = tabulate(
                table_data,
                headers=selected_keys,
                tablefmt="simple",
                stralign="left",
                numalign="left",
            )

        # Add note about hidden columns if any were hidden
        if len(selected_keys) < len(all_keys):
            hidden_count = len(all_keys) - len(selected_keys)
            hidden_cols = [k for k in all_keys if k not in selected_keys]
            formatted_table += f"\n\nNote: {hidden_count} column{'s' if hidden_count != 1 else ''} hidden due to console width: {', '.join(hidden_cols[:3])}{'...' if len(hidden_cols) > 3 else ''}"
            formatted_table += (
                f"\nUse a wider terminal or specify columns with SELECT to see more."
            )

        return formatted_table

    @staticmethod
    def _format_csv(results: List[Dict]) -> str:
        """Format results as CSV"""
        if not results:
            return "No results found"

        output = io.StringIO()

        # Get all fieldnames, preserving order from first result
        fieldnames = []
        seen_keys = set()
        for result in results:
            for key in result.keys():
                if (
                    not key.startswith("_") or key == "_count"
                ) and key not in seen_keys:
                    fieldnames.append(key)
                    seen_keys.add(key)

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
            return "No results found"

        # Get all fieldnames, preserving order from first result
        fieldnames = []
        seen_keys = set()
        for result in results:
            for key in result.keys():
                if (
                    not key.startswith("_") or key == "_count"
                ) and key not in seen_keys:
                    fieldnames.append(key)
                    seen_keys.add(key)

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
        if not paths:
            return "No results found"
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
