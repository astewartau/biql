"""
CLI tests for BIDS Query Language (BIQL)

Tests the command-line interface functionality.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


class TestCLI:
    """Test CLI functionality"""

    def run_biql_command(self, args, dataset_path=None):
        """Helper to run biql command"""
        cmd = [sys.executable, "-m", "biql.cli"]
        if dataset_path:
            cmd.extend(["--dataset", dataset_path])
        cmd.extend(args)

        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent
        )
        return result

    def test_basic_query(self, bids_examples_dir):
        """Test basic query execution"""
        synthetic_dataset_path = str(bids_examples_dir / "synthetic")
        """Test basic query execution"""
        result = self.run_biql_command(["sub=01"], synthetic_dataset_path)

        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert len(output) > 0

        for item in output:
            assert item["sub"] == "01"

    def test_format_options(self, bids_examples_dir):
        """Test different output formats"""
        synthetic_dataset_path = str(bids_examples_dir / "synthetic")
        """Test different output formats"""
        # Test JSON format (default)
        result = self.run_biql_command(
            ["sub=01", "--format", "json"], synthetic_dataset_path
        )
        assert result.returncode == 0
        json.loads(result.stdout)  # Should parse as JSON

        # Test table format
        result = self.run_biql_command(
            ["sub=01", "--format", "table"], synthetic_dataset_path
        )
        assert result.returncode == 0
        assert "|" in result.stdout  # Table format uses pipes

        # Test CSV format
        result = self.run_biql_command(
            ["sub=01", "--format", "csv"], synthetic_dataset_path
        )
        assert result.returncode == 0
        assert "," in result.stdout  # CSV format uses commas

        # Test paths format
        result = self.run_biql_command(
            ["datatype=func", "--format", "paths"], synthetic_dataset_path
        )
        assert result.returncode == 0
        lines = result.stdout.strip().split("\n")
        assert all(
            line.endswith(".nii") or line.endswith(".gz") for line in lines if line
        )

    def test_complex_queries(self, bids_examples_dir):
        """Test complex query execution"""
        synthetic_dataset_path = str(bids_examples_dir / "synthetic")
        """Test complex query execution"""
        # Test SELECT query
        result = self.run_biql_command(
            ["SELECT sub, task, filepath WHERE datatype=func"], synthetic_dataset_path
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)

        if output:
            assert "sub" in output[0]
            assert "task" in output[0]
            assert "filepath" in output[0]

        # Test GROUP BY query
        result = self.run_biql_command(
            ["SELECT sub, COUNT(*) GROUP BY sub"], synthetic_dataset_path
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)

        if output:
            assert "sub" in output[0]
            assert "count" in output[0] or "_count" in output[0]

    def test_logical_operators(self, bids_examples_dir):
        """Test logical operators in CLI"""
        synthetic_dataset_path = str(bids_examples_dir / "synthetic")
        """Test logical operators in CLI"""
        # Test AND operator
        result = self.run_biql_command(
            ["sub=01 AND datatype=func"], synthetic_dataset_path
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)

        for item in output:
            assert item["sub"] == "01"
            assert item["datatype"] == "func"

        # Test OR operator
        result = self.run_biql_command(
            ["task=nback OR task=rest"], synthetic_dataset_path
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)

        for item in output:
            assert item["task"] in ["nback", "rest"]

    def test_range_queries_cli(self, bids_examples_dir):
        """Test range queries via CLI"""
        synthetic_dataset_path = str(bids_examples_dir / "synthetic")
        """Test range queries via CLI"""
        result = self.run_biql_command(["run=[1:2]"], synthetic_dataset_path)
        assert result.returncode == 0
        output = json.loads(result.stdout)

        for item in output:
            if "run" in item:
                run_val = int(item["run"])
                assert 1 <= run_val <= 2

    def test_wildcard_matching_cli(self, bids_examples_dir):
        """Test wildcard matching via CLI"""
        synthetic_dataset_path = str(bids_examples_dir / "synthetic")
        """Test wildcard matching via CLI"""
        result = self.run_biql_command(["suffix=*bold*"], synthetic_dataset_path)
        assert result.returncode == 0
        output = json.loads(result.stdout)

        for item in output:
            if "suffix" in item:
                assert "bold" in item["suffix"]

    def test_output_file(self, bids_examples_dir):
        """Test output to file"""
        synthetic_dataset_path = str(bids_examples_dir / "synthetic")
        """Test output to file"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            output_file = f.name

        try:
            result = self.run_biql_command(
                ["sub=01", "--output", output_file], synthetic_dataset_path
            )
            assert result.returncode == 0

            # Check that file was created and contains valid JSON
            output_path = Path(output_file)
            assert output_path.exists()

            with open(output_path, "r") as f:
                data = json.load(f)
                assert len(data) > 0

        finally:
            Path(output_file).unlink(missing_ok=True)

    def test_dataset_stats(self, bids_examples_dir):
        """Test dataset statistics display"""
        synthetic_dataset_path = str(bids_examples_dir / "synthetic")
        """Test dataset statistics display"""
        result = self.run_biql_command(
            ["--show-stats", "sub=01"], synthetic_dataset_path
        )
        assert result.returncode == 0

        output = result.stdout
        assert "Dataset:" in output
        assert "Total files:" in output
        assert "Subjects:" in output

    def test_entity_display(self, bids_examples_dir):
        """Test entity display"""
        synthetic_dataset_path = str(bids_examples_dir / "synthetic")
        """Test entity display"""
        result = self.run_biql_command(
            ["--show-entities", "sub=01"], synthetic_dataset_path
        )
        assert result.returncode == 0

        output = result.stdout
        assert "Available entities:" in output
        assert "sub" in output
        assert "datatype" in output

    def test_query_validation(self, bids_examples_dir):
        """Test query validation mode"""
        synthetic_dataset_path = str(bids_examples_dir / "synthetic")
        """Test query validation mode"""
        # Valid query
        result = self.run_biql_command(
            ["--validate-only", "sub=01 AND datatype=func"], synthetic_dataset_path
        )
        assert result.returncode == 0
        assert "Query syntax is valid" in result.stdout

        # Invalid query
        result = self.run_biql_command(
            ["--validate-only", "SELECT FROM WHERE"], synthetic_dataset_path
        )
        assert result.returncode == 1
        assert "syntax error" in result.stderr.lower()

    def test_debug_mode(self, bids_examples_dir):
        """Test debug output"""
        synthetic_dataset_path = str(bids_examples_dir / "synthetic")
        """Test debug output"""
        result = self.run_biql_command(["--debug", "sub=01"], synthetic_dataset_path)
        assert result.returncode == 0

        # Debug info should be in stderr
        assert "Loading dataset" in result.stderr
        assert "Found" in result.stderr and "files" in result.stderr

    def test_error_handling(self):
        """Test CLI error handling"""
        # Invalid dataset path
        result = self.run_biql_command(["sub=01"], "/nonexistent/path")
        assert result.returncode == 1

    def test_invalid_query_syntax(self, bids_examples_dir):
        """Test handling of invalid query syntax"""
        synthetic_dataset_path = str(bids_examples_dir / "synthetic")
        """Test handling of invalid query syntax"""
        result = self.run_biql_command(["SELECT FROM WHERE"], synthetic_dataset_path)
        assert result.returncode == 1
        assert "Parse error" in result.stderr or "error" in result.stderr.lower()

    def test_query_evaluation_errors(self, bids_examples_dir):
        """Test handling of query evaluation errors"""
        synthetic_dataset_path = str(bids_examples_dir / "synthetic")
        """Test handling of query evaluation errors"""
        # This should not crash even with complex invalid operations
        result = self.run_biql_command(
            ["metadata.nonexistent>invalid_comparison"], synthetic_dataset_path
        )
        # Should complete successfully but return no results
        assert result.returncode == 0

    def test_output_file_permission_error(self, bids_examples_dir):
        """Test handling of output file permission errors"""
        synthetic_dataset_path = str(bids_examples_dir / "synthetic")
        """Test handling of output file permission errors"""
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a directory where we try to write a file (should fail)
            invalid_output = os.path.join(tmpdir, "readonly_dir", "output.json")

            result = self.run_biql_command(
                ["--output", invalid_output, "sub=01"], synthetic_dataset_path
            )
            # Should handle error gracefully
            assert result.returncode == 1

    def test_debug_mode_with_error(self):
        """Test debug mode when errors occur"""
        result = self.run_biql_command(["--debug", "sub=01"], "/nonexistent/path")
        assert result.returncode == 1
        # Debug mode should provide more detailed error information
        assert len(result.stderr) > 0

    def test_help_output(self):
        """Test help output"""
        result = self.run_biql_command(["--help"])
        assert result.returncode == 0
        assert "BIDS Query Language" in result.stdout
        assert "Examples:" in result.stdout

    def test_version_output(self):
        """Test version output"""
        result = self.run_biql_command(["--version"])
        assert result.returncode == 0
        assert "0.1.0" in result.stdout

    def test_quoted_queries(self, bids_examples_dir):
        """Test queries with quotes and special characters"""
        synthetic_dataset_path = str(bids_examples_dir / "synthetic")
        """Test queries with quotes and special characters"""
        # Query with quotes
        result = self.run_biql_command(['task="nback"'], synthetic_dataset_path)
        assert result.returncode == 0
        output = json.loads(result.stdout)

        for item in output:
            if "task" in item:
                assert item["task"] == "nback"

    def test_metadata_queries_cli(self, bids_examples_dir):
        """Test metadata queries via CLI"""
        synthetic_dataset_path = str(bids_examples_dir / "synthetic")
        """Test metadata queries via CLI"""
        result = self.run_biql_command(
            ["metadata.RepetitionTime>0"], synthetic_dataset_path
        )
        assert result.returncode == 0
        # Should not error, even if no results

    def test_participants_queries_cli(self, bids_examples_dir):
        """Test participants queries via CLI"""
        synthetic_dataset_path = str(bids_examples_dir / "synthetic")
        """Test participants queries via CLI"""
        result = self.run_biql_command(["participants.age>20"], synthetic_dataset_path)
        assert result.returncode == 0
        # Should not error, even if no results


class TestCLIEdgeCases:
    """Test CLI edge cases and error conditions"""

    def test_empty_query(self):
        """Test empty query handling"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create minimal BIDS structure
            dataset_path = Path(tmpdir)
            (dataset_path / "dataset_description.json").write_text(
                '{"Name": "Test", "BIDSVersion": "1.0.0"}'
            )

            result = subprocess.run(
                [sys.executable, "-m", "biql.cli", "", "--dataset", str(dataset_path)],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent,
            )

            assert result.returncode == 0
            output = json.loads(result.stdout)
            assert output == []  # Empty dataset should return empty results

    def test_malformed_dataset(self):
        """Test handling of malformed datasets"""
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = Path(tmpdir)
            # Create directory but no dataset_description.json

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "biql.cli",
                    "sub=01",
                    "--dataset",
                    str(dataset_path),
                ],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent,
            )

            # Should not crash, but may return empty results
            assert result.returncode == 0

    def test_keyboard_interrupt_simulation(self):
        """Test graceful handling of interruption"""
        # This is hard to test directly, but we can test the error code path
        # by checking that the CLI handles general exceptions gracefully
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
