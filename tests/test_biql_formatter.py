"""
Comprehensive tests for BIDS Query Language (BIQL)

Tests all components of the BIQL implementation using real BIDS examples.
"""

import json

import pytest

from biql.formatter import BIQLFormatter


class TestBIQLFormatter:
    """Test BIQL output formatting"""

    def test_json_formatting(self):
        """Test JSON output formatting"""
        results = [
            {"sub": "01", "task": "nback", "filepath": "/path/to/file1.nii"},
            {"sub": "02", "task": "rest", "filepath": "/path/to/file2.nii"},
        ]

        formatted = BIQLFormatter.format(results, "json")
        parsed = json.loads(formatted)

        assert len(parsed) == 2
        assert parsed[0]["sub"] == "01"

    def test_table_formatting(self):
        """Test table output formatting"""
        results = [{"sub": "01", "task": "nback"}, {"sub": "02", "task": "rest"}]

        formatted = BIQLFormatter.format(results, "table")
        lines = formatted.split("\n")

        assert len(lines) >= 4  # Header + separator + 2 data rows
        assert "sub" in lines[0]
        assert "task" in lines[0]
        assert "01" in lines[2] or "01" in lines[3]

    def test_csv_formatting(self):
        """Test CSV output formatting"""
        results = [{"sub": "01", "task": "nback"}, {"sub": "02", "task": "rest"}]

        formatted = BIQLFormatter.format(results, "csv")
        lines = formatted.strip().split("\n")

        assert len(lines) >= 3  # Header + 2 data rows
        assert "sub" in lines[0]
        assert "task" in lines[0]

    def test_paths_formatting(self):
        """Test paths output formatting"""
        results = [
            {"filepath": "/path/to/file1.nii"},
            {"filepath": "/path/to/file2.nii"},
        ]

        formatted = BIQLFormatter.format(results, "paths")
        lines = formatted.strip().split("\n")

        assert len(lines) == 2
        assert "/path/to/file1.nii" in lines
        assert "/path/to/file2.nii" in lines

    def test_empty_results(self):
        """Test formatting empty results"""
        results = []

        json_formatted = BIQLFormatter.format(results, "json")
        assert json_formatted == "[]"

        table_formatted = BIQLFormatter.format(results, "table")
        assert "No results found" in table_formatted

    def test_tsv_formatting(self):
        """Test TSV output formatting"""
        results = [
            {"sub": "01", "task": "nback", "datatype": "func"},
            {"sub": "02", "task": "rest", "datatype": "func"},
        ]

        formatted = BIQLFormatter.format(results, "tsv")
        lines = formatted.strip().split("\n")

        assert len(lines) >= 3  # Header + 2 data rows
        assert "sub" in lines[0]
        assert "task" in lines[0]
        assert "datatype" in lines[0]
        assert "\t" in lines[0]  # TSV should use tabs
        assert "01" in lines[1] or "01" in lines[2]

    def test_unknown_format_fallback(self):
        """Test unknown format falls back to JSON"""
        results = [{"sub": "01", "task": "nback"}]

        formatted = BIQLFormatter.format(results, "unknown_format")
        # Should fall back to JSON format
        parsed = json.loads(formatted)
        assert len(parsed) == 1
        assert parsed[0]["sub"] == "01"

    def test_json_contains_only_select_fields(self):
        """Test that JSON output contains only the fields specified in SELECT, no internal fields"""
        # Create results with only specific fields (no internal fields should be present)
        results = [
            {"sub": "01", "task": "nback", "total_files": 5},
            {"sub": "02", "task": "rest", "total_files": 3},
        ]

        formatted = BIQLFormatter.format(results, "json")
        parsed = json.loads(formatted)

        # Verify structure and content
        assert len(parsed) == 2

        # Each result should contain exactly the expected fields, no more
        for result in parsed:
            assert set(result.keys()) == {"sub", "task", "total_files"}
            assert "sub" in result
            assert "task" in result
            assert "total_files" in result

            # Most importantly: no internal fields should be present
            for key in result.keys():
                assert not key.startswith(
                    "_"
                ), f"Found internal field '{key}' in JSON output"

    def test_complex_value_formatting(self):
        """Test formatting of complex values (lists, nested dicts)"""
        results = [
            {
                "sub": "01",
                "files": ["file1.nii", "file2.nii"],
                "metadata": {"RepetitionTime": 2.0, "EchoTime": 0.03},
            }
        ]

        # Test JSON formatting with complex values
        json_formatted = BIQLFormatter.format(results, "json")
        parsed = json.loads(json_formatted)
        assert isinstance(parsed[0]["files"], list)
        assert len(parsed[0]["files"]) == 2

        # Test table formatting with complex values
        table_formatted = BIQLFormatter.format(results, "table")
        # Complex values might be displayed as [...] or {... keys...} in table format
        assert "sub" in table_formatted and "01" in table_formatted

        # Test CSV formatting with complex values
        csv_formatted = BIQLFormatter.format(results, "csv")
        assert "file1.nii" in csv_formatted

    def test_paths_formatting_edge_cases(self):
        """Test paths output formatting with edge cases"""
        # Test with relative_path fallback
        results = [
            {"relative_path": "sub-01/func/sub-01_task-nback_bold.nii"},
            {
                "filepath": "/absolute/path/file.nii",
                "relative_path": "sub-02/func/file.nii",
            },
        ]

        formatted = BIQLFormatter.format(results, "paths")
        lines = formatted.strip().split("\n")

        assert len(lines) == 2
        assert "sub-01/func/sub-01_task-nback_bold.nii" in lines
        assert "/absolute/path/file.nii" in lines

    def test_csv_formatting_edge_cases(self):
        """Test CSV formatting with edge cases"""
        results = [
            {"sub": "01", "value": None},
            {"sub": "02", "value": True},
            {"sub": "03", "value": 123},
            {"sub": "04", "value": ["a", "b"]},
        ]

        formatted = BIQLFormatter.format(results, "csv")
        lines = formatted.strip().split("\n")

        # Check header
        assert "sub" in lines[0]
        assert "value" in lines[0]

        # Check that different value types are handled
        assert len(lines) >= 5  # Header + 4 data rows

    def test_empty_keys_handling(self):
        """Test handling of empty or missing keys"""
        results = [
            {"sub": "01"},  # Missing some fields
            {"sub": "02", "task": "nback"},  # Different fields
            {},  # Empty dict
        ]

        # Should not crash on any format
        for format_type in ["json", "table", "csv", "tsv"]:
            formatted = BIQLFormatter.format(results, format_type)
            assert isinstance(formatted, str)
            # Some formats might return empty string for empty data, that's OK

        # Paths format might return empty for results without filepath/relative_path
        paths_formatted = BIQLFormatter.format(results, "paths")

    def test_paths_formatting_grouped_results(self):
        """Test paths formatting with grouped results (arrays)"""
        grouped_results = [
            {
                "sub": "01",
                "filename": ["sub-01_task-rest_bold.nii", "sub-01_task-nback_bold.nii"],
            },
            {
                "sub": "02",
                "filepath": [
                    "/data/sub-02_task-rest_bold.nii",
                    "/data/sub-02_task-nback_bold.nii",
                ],
            },
        ]

        paths_output = BIQLFormatter.format(grouped_results, "paths")
        lines = paths_output.strip().split("\n")

        # Should extract all filenames/filepaths from arrays
        assert len(lines) == 4
        assert "sub-01_task-rest_bold.nii" in lines
        assert "sub-01_task-nback_bold.nii" in lines
        assert "/data/sub-02_task-rest_bold.nii" in lines
        assert "/data/sub-02_task-nback_bold.nii" in lines

    def test_paths_formatting_with_original_files(self):
        """Test paths formatting uses original files regardless of selected fields"""

        # Mock file objects for the original files parameter
        class MockFile:
            def __init__(self, filepath):
                self.filepath = filepath

        original_files = [
            MockFile("/data/sub-01_task-rest_bold.nii"),
            MockFile("/data/sub-01_task-nback_bold.nii"),
            MockFile("/data/sub-02_task-rest_bold.nii"),
        ]

        # Results only contain selected fields (no _file_paths)
        results = [
            {"sub": "01"},
            {"task": "rest"},
        ]

        paths_output = BIQLFormatter.format(results, "paths", original_files)
        lines = paths_output.strip().split("\n")

        # Should use the original files and be sorted
        assert len(lines) == 3
        assert lines[0] == "/data/sub-01_task-nback_bold.nii"  # nback comes before rest
        assert lines[1] == "/data/sub-01_task-rest_bold.nii"
        assert lines[2] == "/data/sub-02_task-rest_bold.nii"


if __name__ == "__main__":
    # Run specific test categories
    pytest.main([__file__, "-v", "--tb=short"])
