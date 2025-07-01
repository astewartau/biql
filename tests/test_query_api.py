"""
Tests for the high-level BIQL Query API
"""

import json
import tempfile
from pathlib import Path

import pytest

from biql.query import BIQLQuery, create_query_engine


class DatasetInfo:
    """Helper class to store dataset path and expected counts"""

    def __init__(self, path, expected_total_files, expected_func_files):
        self.path = path
        self.expected_total_files = expected_total_files
        self.expected_func_files = expected_func_files


class TestBIQLQueryAPI:
    """Test the high-level BIQL query API"""

    @pytest.fixture
    def test_dataset(self):
        """Create a minimal test dataset"""
        tmpdir = Path(tempfile.mkdtemp())

        # Dataset description
        (tmpdir / "dataset_description.json").write_text(
            json.dumps({"Name": "Test", "BIDSVersion": "1.8.0"})
        )

        # Participants file
        (tmpdir / "participants.tsv").write_text(
            "participant_id\tage\tsex\n" "sub-01\t25\tF\n" "sub-02\t30\tM\n"
        )

        # Create test files
        files = [
            "sub-01/anat/sub-01_T1w.nii.gz",
            "sub-01/func/sub-01_task-rest_bold.nii.gz",
            "sub-02/anat/sub-02_T1w.nii.gz",
            "sub-02/func/sub-02_task-rest_bold.nii.gz",
        ]

        # Track total files (data + JSON)
        total_files_created = 0
        func_files_created = 0

        for file_path in files:
            full_path = tmpdir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.touch()
            total_files_created += 1

            # Create JSON metadata for functional files
            if "bold" in file_path:
                json_path = full_path.with_suffix(".json")
                json_path.write_text(
                    json.dumps({"RepetitionTime": 2.0, "TaskName": "rest"})
                )
                total_files_created += 1  # Count the JSON file
                func_files_created += 2  # .nii.gz + .json
            elif "T1w" in file_path:
                func_files_created += 0  # No extra JSON for T1w in this test

        # Return dataset info with expected counts
        return DatasetInfo(
            path=tmpdir,
            expected_total_files=total_files_created,  # 4 data + 2 JSON = 6
            expected_func_files=func_files_created,  # 2 .nii.gz + 2 .json = 4
        )

    def test_create_query_engine(self, test_dataset):
        """Test creating query engine with convenience function"""
        biql = create_query_engine(test_dataset.path)
        assert isinstance(biql, BIQLQuery)
        assert biql.default_format == "json"

        # Test with custom default format
        biql_table = create_query_engine(test_dataset.path, default_format="table")
        assert biql_table.default_format == "table"

    def test_basic_query_json_format(self, test_dataset):
        """Test basic query with JSON format"""
        biql = create_query_engine(test_dataset.path)
        results = biql.run_query("sub=01")

        assert isinstance(results, list)
        # Subject 01 has: 1 T1w.nii.gz + 1 bold.nii.gz + 1 bold.json = 3 files
        assert len(results) == 3
        assert all("sub" in r and r["sub"] == "01" for r in results)

    def test_query_with_format_override(self, test_dataset):
        """Test format override functionality"""
        biql = create_query_engine(test_dataset.path, default_format="json")

        # Override to table format
        table_result = biql.run_query("SELECT sub, datatype", format="table")
        assert isinstance(table_result, str)
        assert "sub" in table_result and "datatype" in table_result

    def test_dataframe_format(self, test_dataset):
        """Test DataFrame output format"""
        biql = create_query_engine(test_dataset.path)

        try:
            import pandas as pd
        except ImportError:
            pytest.skip("pandas not available")

        df = biql.run_query("SELECT sub, datatype", format="dataframe")
        assert hasattr(df, "columns")  # pandas DataFrame
        assert "sub" in df.columns
        assert "datatype" in df.columns
        assert len(df) == test_dataset.expected_total_files  # All files (6 total)

    def test_dataframe_format_without_pandas(self, test_dataset):
        """Test DataFrame format raises appropriate error without pandas"""
        biql = create_query_engine(test_dataset.path)

        # Mock pandas import failure by patching the import in the query module
        import sys
        from unittest.mock import patch

        # Patch the pandas import to raise ImportError
        with patch.dict(sys.modules, {"pandas": None}):
            with patch("builtins.__import__") as mock_import:

                def side_effect(name, *args, **kwargs):
                    if name == "pandas":
                        raise ImportError("No module named 'pandas'")
                    return __import__(name, *args, **kwargs)

                mock_import.side_effect = side_effect

                with pytest.raises(ImportError, match="pandas is required"):
                    biql.run_query("SELECT sub", format="dataframe")

    def test_all_output_formats(self, test_dataset):
        """Test all supported output formats"""
        biql = create_query_engine(test_dataset.path)
        query = "SELECT sub, datatype"

        # JSON format (default)
        json_results = biql.run_query(query)
        assert isinstance(json_results, list)

        # String formats
        for fmt in ["table", "csv", "tsv", "paths"]:
            result = biql.run_query(query, format=fmt)
            assert isinstance(result, str)

    def test_helper_methods(self, test_dataset):
        """Test helper methods"""
        biql = create_query_engine(test_dataset.path)

        # Test get_subjects
        subjects = biql.get_subjects()
        assert subjects == ["01", "02"]

        # Test get_datatypes
        datatypes = biql.get_datatypes()
        assert "anat" in datatypes
        assert "func" in datatypes

        # Test get_entities
        entities = biql.get_entities()
        assert "sub" in entities
        assert "datatype" in entities
        assert "task" in entities

        # Test dataset_stats
        stats = biql.dataset_stats()
        assert "total_files" in stats
        assert "total_subjects" in stats
        assert (
            stats["total_files"] == test_dataset.expected_total_files
        )  # Exactly 6 files
        assert stats["total_subjects"] == 2

    def test_complex_queries(self, test_dataset):
        """Test complex queries with new API"""
        biql = create_query_engine(test_dataset.path)

        # Test GROUP BY
        results = biql.run_query("SELECT datatype, COUNT(*) GROUP BY datatype")
        assert len(results) == 2  # anat and func

        # Test with metadata
        results = biql.run_query("SELECT metadata.RepetitionTime WHERE datatype=func")
        assert (
            len(results) == test_dataset.expected_func_files
        )  # Exactly 4 func files (2 .nii.gz + 2 .json)

        # Test aggregation by participant sex (just verify it works)
        results = biql.run_query(
            "SELECT participants.sex, COUNT(*) GROUP BY participants.sex"
        )
        # Should have 2 groups: F and M
        assert len(results) == 2
        sex_groups = {
            r["participants.sex"]: r["count"]
            for r in results
            if "participants.sex" in r
        }
        # Each sex should have 3 files (1 anat + 1 func + 1 JSON)
        assert sex_groups.get("F") == 3  # sub-01 files
        assert sex_groups.get("M") == 3  # sub-02 files

    def test_dataframe_metadata_flattening(self, test_dataset):
        """Test that DataFrame format properly handles nested data"""
        try:
            import pandas as pd
        except ImportError:
            pytest.skip("pandas not available")

        biql = create_query_engine(test_dataset.path)

        # Query with metadata
        df = biql.run_query(
            "SELECT sub, metadata.RepetitionTime WHERE datatype=func",
            format="dataframe",
        )

        # Check that metadata fields are properly handled
        assert "sub" in df.columns
        assert "metadata.RepetitionTime" in df.columns
        assert len(df) == test_dataset.expected_func_files  # Exactly 4 func files

    def test_range_syntax_bug(self):
        """Test the reported bug: run=[1:2] returns [] while run IN [1,2] works"""
        # Create test dataset with run values to reproduce the exact bug
        tmpdir = Path(tempfile.mkdtemp())

        # Dataset description
        (tmpdir / "dataset_description.json").write_text(
            json.dumps({"Name": "Test", "BIDSVersion": "1.8.0"})
        )

        # Create files with run values
        for sub in ["01", "02"]:
            for run in ["01", "02", "03"]:
                func_dir = tmpdir / f"sub-{sub}" / "func"
                func_dir.mkdir(parents=True, exist_ok=True)
                filename = f"sub-{sub}_task-test_run-{run}_bold.nii"
                (func_dir / filename).touch()

        # Create query engine like the notebook does
        biql = create_query_engine(tmpdir)

        # Test range syntax [1:2] - user reported this returns []
        results_range = biql.run_query("SELECT sub WHERE run=[1:2]", format="json")

        # Test IN syntax [1,2] - user reported this works
        results_in = biql.run_query("SELECT sub WHERE run IN [1,2]", format="json")

        # IN should work and return 4 results (2 subjects × 2 runs)
        assert (
            len(results_in) == 4
        ), f"Expected 4 results from IN syntax, got {len(results_in)}"

        # Range should return the same but currently returns []
        assert (
            len(results_range) == 4
        ), f"Range syntax [1:2] should return 4 results but returned {len(results_range)}"

        # Results should be identical
        subs_range = sorted([r["sub"] for r in results_range])
        subs_in = sorted([r["sub"] for r in results_in])
        assert (
            subs_range == subs_in
        ), f"Range returned {subs_range}, IN returned {subs_in}"

    def test_error_handling(self, test_dataset):
        """Test error handling in query API"""
        biql = create_query_engine(test_dataset.path)

        # Invalid query should raise parse error
        with pytest.raises(Exception):  # BIQLParseError
            biql.run_query("SELECT FROM WHERE")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
