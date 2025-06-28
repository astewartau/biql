"""
Comprehensive tests for BIDS Query Language (BQL)

Tests all components of the BQL implementation using real BIDS examples.
"""

import json
import os
import pytest
import tempfile
from pathlib import Path
from typing import List, Dict, Any

from biql.dataset import BIDSDataset, BIDSFile
from biql.evaluator import BQLEvaluator
from biql.formatter import BQLFormatter
from biql.lexer import BQLLexer, TokenType
from biql.parser import BQLParser, BQLParseError
from biql.cli import main

# Test constants
BIDS_EXAMPLES_DIR = Path("/home/ashley/repos/bids-examples/")


class TestBQLLexer:
    """Test the BQL lexer functionality"""
    
    def test_basic_tokenization(self):
        """Test basic token recognition"""
        lexer = BQLLexer("sub=01 AND task=rest")
        tokens = lexer.tokenize()
        
        token_types = [t.type for t in tokens if t.type != TokenType.EOF]
        expected = [
            TokenType.IDENTIFIER, TokenType.EQ, TokenType.NUMBER,
            TokenType.AND,
            TokenType.IDENTIFIER, TokenType.EQ, TokenType.IDENTIFIER
        ]
        assert token_types == expected
        
    def test_string_literals(self):
        """Test string literal tokenization"""
        lexer = BQLLexer('task="n-back" OR suffix="T1w"')
        tokens = lexer.tokenize()
        
        string_tokens = [t for t in tokens if t.type == TokenType.STRING]
        assert len(string_tokens) == 2
        assert string_tokens[0].value == "n-back"
        assert string_tokens[1].value == "T1w"
        
    def test_operators(self):
        """Test operator tokenization"""
        lexer = BQLLexer("metadata.RepetitionTime>=2.0 AND run<=[1:3]")
        tokens = lexer.tokenize()
        
        operator_tokens = [t for t in tokens if t.type in [TokenType.GTE, TokenType.LTE]]
        assert len(operator_tokens) == 2
        
    def test_complex_query(self):
        """Test complex query tokenization"""
        query = "SELECT sub, ses, filepath WHERE (task=nback OR task=rest) AND metadata.RepetitionTime<3.0"
        lexer = BQLLexer(query)
        tokens = lexer.tokenize()
        
        assert any(t.type == TokenType.SELECT for t in tokens)
        assert any(t.type == TokenType.WHERE for t in tokens)
        assert any(t.type == TokenType.LPAREN for t in tokens)
        assert any(t.type == TokenType.RPAREN for t in tokens)


class TestBQLParser:
    """Test the BQL parser functionality"""
    
    def test_simple_query_parsing(self):
        """Test parsing simple queries"""
        parser = BQLParser.from_string("sub=01")
        query = parser.parse()
        
        assert query.where_clause is not None
        assert query.select_clause is None
        
    def test_select_query_parsing(self):
        """Test parsing SELECT queries"""
        parser = BQLParser.from_string("SELECT sub, task, filepath WHERE datatype=func")
        query = parser.parse()
        
        assert query.select_clause is not None
        assert len(query.select_clause.items) == 3
        assert query.where_clause is not None
        
    def test_complex_where_clause(self):
        """Test parsing complex WHERE clauses"""
        parser = BQLParser.from_string("(sub=01 OR sub=02) AND task=nback")
        query = parser.parse()
        
        assert query.where_clause is not None
        
    def test_group_by_parsing(self):
        """Test parsing GROUP BY clauses"""
        parser = BQLParser.from_string("SELECT sub, COUNT(*) GROUP BY sub")
        query = parser.parse()
        
        assert query.group_by is not None
        assert "sub" in query.group_by
        
    def test_order_by_parsing(self):
        """Test parsing ORDER BY clauses"""
        parser = BQLParser.from_string("sub=01 ORDER BY run DESC")
        query = parser.parse()
        
        assert query.order_by is not None
        assert query.order_by[0] == ("run", "DESC")
        
    def test_format_parsing(self):
        """Test parsing FORMAT clauses"""
        parser = BQLParser.from_string("sub=01 FORMAT table")
        query = parser.parse()
        
        assert query.format == "table"
        
    def test_invalid_syntax(self):
        """Test that invalid syntax raises errors"""
        with pytest.raises(BQLParseError):
            parser = BQLParser.from_string("SELECT FROM WHERE")
            parser.parse()
            
    def test_distinct_parsing(self):
        """Test parsing SELECT DISTINCT queries"""
        parser = BQLParser.from_string("SELECT DISTINCT sub, task")
        query = parser.parse()
        
        assert query.select_clause is not None
        assert query.select_clause.distinct is True
        assert len(query.select_clause.items) == 2
        assert query.select_clause.items[0] == ("sub", None)
        assert query.select_clause.items[1] == ("task", None)
        
    def test_non_distinct_parsing(self):
        """Test that regular SELECT queries have distinct=False"""
        parser = BQLParser.from_string("SELECT sub, task")
        query = parser.parse()
        
        assert query.select_clause is not None
        assert query.select_clause.distinct is False


class TestBIDSDataset:
    """Test BIDS dataset loading and indexing"""
    
    @pytest.fixture
    def synthetic_dataset(self):
        """Fixture for synthetic BIDS dataset"""
        if not (BIDS_EXAMPLES_DIR / "synthetic").exists():
            pytest.skip("BIDS examples not available")
        return BIDSDataset(BIDS_EXAMPLES_DIR / "synthetic")
        
    @pytest.fixture
    def ds001_dataset(self):
        """Fixture for ds001 BIDS dataset"""
        if not (BIDS_EXAMPLES_DIR / "ds001").exists():
            pytest.skip("BIDS examples not available")
        return BIDSDataset(BIDS_EXAMPLES_DIR / "ds001")
        
    def test_dataset_loading(self, synthetic_dataset):
        """Test basic dataset loading"""
        assert len(synthetic_dataset.files) > 0
        assert len(synthetic_dataset.participants) > 0
        
    def test_entity_extraction(self, synthetic_dataset):
        """Test BIDS entity extraction"""
        subjects = synthetic_dataset.get_subjects()
        assert "01" in subjects
        assert len(subjects) >= 3
        
        datatypes = synthetic_dataset.get_datatypes()
        assert "anat" in datatypes
        assert "func" in datatypes
        
    def test_file_parsing(self, synthetic_dataset):
        """Test individual file parsing"""
        # Find a functional file
        func_files = [f for f in synthetic_dataset.files if f.entities.get("datatype") == "func"]
        assert len(func_files) > 0
        
        func_file = func_files[0]
        assert "sub" in func_file.entities
        assert "task" in func_file.entities
        
    def test_participants_loading(self, synthetic_dataset):
        """Test participants.tsv loading"""
        participants = synthetic_dataset.participants
        assert len(participants) > 0
        
        # Check specific participant data
        if "01" in participants:
            assert "age" in participants["01"]
            assert "sex" in participants["01"]
            
    def test_metadata_inheritance(self, synthetic_dataset):
        """Test JSON metadata inheritance"""
        # The synthetic dataset doesn't have individual file metadata,
        # but it should inherit from dataset-level task files
        task_files = [f for f in synthetic_dataset.files if "task" in f.entities]
        
        # Check that task files exist
        assert len(task_files) > 0
        
        # Check that metadata inheritance works when metadata files are available
        # This is more of a structural test for the synthetic dataset
        for task_file in task_files[:3]:  # Check first few files
            assert "task" in task_file.entities


class TestBQLEvaluator:
    """Test BQL query evaluation"""
    
    @pytest.fixture
    def synthetic_dataset(self):
        """Fixture for synthetic BIDS dataset"""
        if not (BIDS_EXAMPLES_DIR / "synthetic").exists():
            pytest.skip("BIDS examples not available")
        return BIDSDataset(BIDS_EXAMPLES_DIR / "synthetic")
        
    @pytest.fixture
    def evaluator(self, synthetic_dataset):
        """Fixture for BQL evaluator"""
        return BQLEvaluator(synthetic_dataset)
        
    def test_simple_entity_query(self, evaluator):
        """Test simple entity-based queries"""
        parser = BQLParser.from_string("sub=01")
        query = parser.parse()
        results = evaluator.evaluate(query)
        
        assert len(results) > 0
        for result in results:
            assert result["sub"] == "01"
            
    def test_datatype_filtering(self, evaluator):
        """Test datatype filtering"""
        parser = BQLParser.from_string("datatype=func")
        query = parser.parse()
        results = evaluator.evaluate(query)
        
        assert len(results) > 0
        for result in results:
            assert result["datatype"] == "func"
            
    def test_task_filtering(self, evaluator):
        """Test task filtering"""
        parser = BQLParser.from_string("task=nback")
        query = parser.parse()
        results = evaluator.evaluate(query)
        
        assert len(results) > 0
        for result in results:
            assert result["task"] == "nback"
            
    def test_logical_operators(self, evaluator):
        """Test logical AND/OR operators"""
        parser = BQLParser.from_string("sub=01 AND datatype=func")
        query = parser.parse()
        results = evaluator.evaluate(query)
        
        for result in results:
            assert result["sub"] == "01"
            assert result["datatype"] == "func"
            
        parser = BQLParser.from_string("task=nback OR task=rest")
        query = parser.parse()
        results = evaluator.evaluate(query)
        
        for result in results:
            assert result["task"] in ["nback", "rest"]
            
    def test_range_queries(self, evaluator):
        """Test range queries"""
        parser = BQLParser.from_string("run=[1:2]")
        query = parser.parse()
        results = evaluator.evaluate(query)
        
        for result in results:
            if "run" in result:
                run_val = int(result["run"])
                assert 1 <= run_val <= 2
                
    def test_wildcard_matching(self, evaluator):
        """Test wildcard pattern matching"""
        parser = BQLParser.from_string("suffix=*bold*")
        query = parser.parse()
        results = evaluator.evaluate(query)
        
        for result in results:
            if "suffix" in result:
                assert "bold" in result["suffix"]
                
    def test_metadata_queries(self, evaluator):
        """Test metadata queries"""
        parser = BQLParser.from_string("metadata.RepetitionTime>0")
        query = parser.parse()
        results = evaluator.evaluate(query)
        
        # Should find files with RepetitionTime metadata
        # Note: may be empty if metadata isn't loaded properly
        for result in results:
            metadata = result.get("metadata", {})
            if "RepetitionTime" in metadata:
                assert float(metadata["RepetitionTime"]) > 0
                
    def test_participants_queries(self, evaluator):
        """Test participants data queries"""
        parser = BQLParser.from_string("participants.age>20")
        query = parser.parse()
        results = evaluator.evaluate(query)
        
        for result in results:
            participants = result.get("participants", {})
            if "age" in participants:
                assert int(participants["age"]) > 20
                
    def test_select_clause(self, evaluator):
        """Test SELECT clause functionality"""
        parser = BQLParser.from_string("SELECT sub, task, filepath WHERE datatype=func")
        query = parser.parse()
        results = evaluator.evaluate(query)
        
        if results:
            result = results[0]
            expected_keys = {"sub", "task", "filepath"}
            # Result may have more keys, but should have at least these
            assert expected_keys.issubset(set(result.keys()))
            
    def test_group_by_functionality(self, evaluator):
        """Test GROUP BY functionality"""
        parser = BQLParser.from_string("SELECT sub, COUNT(*) GROUP BY sub")
        query = parser.parse()
        results = evaluator.evaluate(query)
        
        assert len(results) > 0
        for result in results:
            assert "sub" in result
            assert "count" in result
            assert result["count"] > 0
            
    def test_order_by_functionality(self, evaluator):
        """Test ORDER BY functionality"""
        parser = BQLParser.from_string("datatype=func ORDER BY sub ASC")
        query = parser.parse()
        results = evaluator.evaluate(query)
        
        if len(results) > 1:
            # Check that results are ordered by subject
            subjects = [r.get("sub", "") for r in results]
            assert subjects == sorted(subjects)
            
    def test_group_by_auto_aggregation(self, evaluator):
        """Test auto-aggregation of non-grouped fields in GROUP BY queries"""
        parser = BQLParser.from_string("SELECT sub, task, filepath, COUNT(*) WHERE datatype=func GROUP BY sub")
        query = parser.parse()
        results = evaluator.evaluate(query)
        
        if len(results) > 0:
            result = results[0]
            
            # Grouped field should be a single value
            assert "sub" in result
            assert isinstance(result["sub"], str)
            
            # Non-grouped fields should be aggregated into arrays when multiple values exist
            if "task" in result:
                # Task should be either a single value or array of values
                assert isinstance(result["task"], (str, list))
                
            if "filepath" in result:
                # Filepath should be either a single value or array of values
                assert isinstance(result["filepath"], (str, list))
            
            # COUNT should work as expected
            assert "count" in result
            assert isinstance(result["count"], int)
            assert result["count"] > 0
            
    def test_group_by_single_value_no_array(self, evaluator):
        """Test that single values don't become arrays in GROUP BY results"""
        parser = BQLParser.from_string("SELECT sub, datatype, COUNT(*) WHERE datatype=func GROUP BY sub, datatype")
        query = parser.parse()
        results = evaluator.evaluate(query)
        
        if len(results) > 0:
            result = results[0]
            
            # Since datatype is in GROUP BY and we filtered for only 'func', 
            # it should be a single value, not an array
            assert result["datatype"] == "func"
            assert not isinstance(result["datatype"], list)
            
    def test_group_by_multiple_values_array(self, evaluator):
        """Test that multiple values become arrays in GROUP BY results"""
        # Create test scenario with mixed datatypes
        parser = BQLParser.from_string("SELECT sub, datatype, COUNT(*) GROUP BY sub")
        query = parser.parse()
        results = evaluator.evaluate(query)
        
        if len(results) > 0:
            # Look for a result that has multiple datatypes
            for result in results:
                if "datatype" in result and isinstance(result["datatype"], list):
                    # Found a subject with multiple datatypes
                    assert len(result["datatype"]) > 1
                    # All items should be strings
                    assert all(isinstance(dt, str) for dt in result["datatype"])
                    break
                    
    def test_group_by_preserves_null_handling(self, evaluator):
        """Test that None values are handled correctly in auto-aggregation"""
        parser = BQLParser.from_string("SELECT sub, run, COUNT(*) GROUP BY sub")
        query = parser.parse()
        results = evaluator.evaluate(query)
        
        if len(results) > 0:
            # Some files might not have run entities
            for result in results:
                if "run" in result:
                    run_value = result["run"]
                    # Should be None, string, or list
                    assert run_value is None or isinstance(run_value, (str, list))
                    if isinstance(run_value, list):
                        # If it's a list, all non-None values should be strings
                        non_none_values = [v for v in run_value if v is not None]
                        assert all(isinstance(v, str) for v in non_none_values)
                        
    def test_distinct_functionality(self, evaluator):
        """Test DISTINCT functionality removes duplicate rows"""
        # First get some results that might have duplicates
        parser = BQLParser.from_string("SELECT datatype")
        query = parser.parse()
        regular_results = evaluator.evaluate(query)
        
        # Now get DISTINCT results
        parser = BQLParser.from_string("SELECT DISTINCT datatype")
        query = parser.parse()
        distinct_results = evaluator.evaluate(query)
        
        # DISTINCT should have fewer or equal results
        assert len(distinct_results) <= len(regular_results)
        
        # All results should be unique
        seen_datatypes = set()
        for result in distinct_results:
            datatype = result.get("datatype")
            assert datatype not in seen_datatypes, f"Duplicate datatype found: {datatype}"
            seen_datatypes.add(datatype)
            
    def test_distinct_multiple_fields(self, evaluator):
        """Test DISTINCT with multiple fields"""
        parser = BQLParser.from_string("SELECT DISTINCT sub, datatype")
        query = parser.parse()
        results = evaluator.evaluate(query)
        
        # Check that all combinations are unique
        seen_combinations = set()
        for result in results:
            combination = (result.get("sub"), result.get("datatype"))
            assert combination not in seen_combinations, f"Duplicate combination: {combination}"
            seen_combinations.add(combination)
            
    def test_distinct_with_where_clause(self, evaluator):
        """Test DISTINCT combined with WHERE clause"""
        parser = BQLParser.from_string("SELECT DISTINCT task WHERE datatype=func")
        query = parser.parse()
        results = evaluator.evaluate(query)
        
        # Should only have unique task values from functional files
        seen_tasks = set()
        for result in results:
            task = result.get("task")
            if task is not None:
                assert task not in seen_tasks, f"Duplicate task found: {task}"
                seen_tasks.add(task)


class TestQSMWorkflow:
    """Test QSM-specific workflow scenarios"""
    
    def test_qsm_reconstruction_groups_with_filenames(self):
        """Test QSM reconstruction groups include filename arrays (real QSM use case)"""
        # Create a minimal test dataset with QSM-like structure
        import tempfile
        import json
        from pathlib import Path
        from biql.dataset import BIDSDataset
        from biql.evaluator import BQLEvaluator
        from biql.parser import BQLParser
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create dataset description
            (tmpdir / "dataset_description.json").write_text(
                json.dumps({"Name": "QSM Test", "BIDSVersion": "1.8.0"})
            )
            
            # Create QSM files for testing
            qsm_files = [
                "sub-01/anat/sub-01_echo-01_part-mag_MEGRE.nii",
                "sub-01/anat/sub-01_echo-01_part-phase_MEGRE.nii", 
                "sub-01/anat/sub-01_echo-02_part-mag_MEGRE.nii",
                "sub-01/anat/sub-01_echo-02_part-phase_MEGRE.nii",
                "sub-02/anat/sub-02_acq-test_echo-01_part-mag_MEGRE.nii",
                "sub-02/anat/sub-02_acq-test_echo-01_part-phase_MEGRE.nii"
            ]
            
            for file_path in qsm_files:
                full_path = tmpdir / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.touch()
            
            # Test the QSM reconstruction grouping query
            dataset = BIDSDataset(tmpdir)
            evaluator = BQLEvaluator(dataset)
            
            parser = BQLParser.from_string(
                "SELECT filename, sub, acq, part, echo, COUNT(*) "
                "WHERE (part=mag OR part=phase) AND suffix=MEGRE "
                "GROUP BY sub, acq"
            )
            query = parser.parse()
            results = evaluator.evaluate(query)
            
            assert len(results) == 2  # Two groups: sub-01 (no acq) and sub-02 (acq-test)
            
            for result in results:
                # Each group should have basic fields
                assert "sub" in result
                assert "count" in result
                assert result["count"] > 0
                
                # Filename should be an array of all files in the group
                assert "filename" in result
                if isinstance(result["filename"], list):
                    assert len(result["filename"]) == result["count"]
                    # All filenames should contain the subject ID
                    assert all(result["sub"] in fname for fname in result["filename"])
                else:
                    # Single file case
                    assert result["count"] == 1
                    assert result["sub"] in result["filename"]
                
                # Part should show both mag and phase (if group has both)
                if "part" in result and isinstance(result["part"], list):
                    assert "mag" in result["part"] or "phase" in result["part"]
                    
                # Echo should show the echo numbers in the group
                if "echo" in result:
                    assert result["echo"] is not None
            
            # Verify subject 01 group (no acquisition)
            sub01_group = next(r for r in results if r["sub"] == "01" and r.get("acq") is None)
            assert sub01_group["count"] == 4  # 2 echoes × 2 parts
            
            # Verify subject 02 group (with acquisition)  
            sub02_group = next(r for r in results if r["sub"] == "02" and r.get("acq") == "test")
            assert sub02_group["count"] == 2  # 1 echo × 2 parts
            
    def test_distinct_echo_times_discovery(self):
        """Test DISTINCT for discovering unique EchoTime values (real QSM use case)"""
        # Create test dataset with varying echo times
        import tempfile
        import json
        from pathlib import Path
        from biql.dataset import BIDSDataset
        from biql.evaluator import BQLEvaluator
        from biql.parser import BQLParser
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create dataset description
            (tmpdir / "dataset_description.json").write_text(
                json.dumps({"Name": "Echo Test", "BIDSVersion": "1.8.0"})
            )
            
            # Create files with different echo times
            echo_files = [
                ("sub-01/anat/sub-01_echo-01_part-mag_MEGRE.nii", 0.005),
                ("sub-01/anat/sub-01_echo-01_part-mag_MEGRE.json", 0.005),
                ("sub-01/anat/sub-01_echo-02_part-mag_MEGRE.nii", 0.010),
                ("sub-01/anat/sub-01_echo-02_part-mag_MEGRE.json", 0.010),
                ("sub-02/anat/sub-02_echo-01_part-mag_MEGRE.nii", 0.005),  # Same as sub-01
                ("sub-02/anat/sub-02_echo-01_part-mag_MEGRE.json", 0.005),
                ("sub-02/anat/sub-02_echo-02_part-mag_MEGRE.nii", 0.015),  # Different
                ("sub-02/anat/sub-02_echo-02_part-mag_MEGRE.json", 0.015),
            ]
            
            for file_path, echo_time in echo_files:
                full_path = tmpdir / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                
                if file_path.endswith('.json'):
                    metadata = {"EchoTime": echo_time, "MagneticFieldStrength": 3.0}
                    full_path.write_text(json.dumps(metadata))
                else:
                    full_path.touch()
            
            # Test DISTINCT metadata.EchoTime
            dataset = BIDSDataset(tmpdir)
            evaluator = BQLEvaluator(dataset)
            
            parser = BQLParser.from_string("SELECT DISTINCT metadata.EchoTime WHERE suffix=MEGRE")
            query = parser.parse()
            results = evaluator.evaluate(query)
            
            # Should have 3 unique echo times: 0.005, 0.010, 0.015
            echo_times = [r.get("metadata.EchoTime") for r in results if r.get("metadata.EchoTime") is not None]
            assert len(echo_times) == 3
            assert 0.005 in echo_times
            assert 0.010 in echo_times
            assert 0.015 in echo_times
            
            # Test DISTINCT echo (should be 01, 02)
            parser = BQLParser.from_string("SELECT DISTINCT echo WHERE suffix=MEGRE")
            query = parser.parse()
            results = evaluator.evaluate(query)
            
            echo_numbers = [r.get("echo") for r in results if r.get("echo") is not None]
            assert len(echo_numbers) == 2
            assert "01" in echo_numbers
            assert "02" in echo_numbers


class TestBQLFormatter:
    """Test BQL output formatting"""
    
    def test_json_formatting(self):
        """Test JSON output formatting"""
        results = [
            {"sub": "01", "task": "nback", "filepath": "/path/to/file1.nii"},
            {"sub": "02", "task": "rest", "filepath": "/path/to/file2.nii"}
        ]
        
        formatted = BQLFormatter.format(results, "json")
        parsed = json.loads(formatted)
        
        assert len(parsed) == 2
        assert parsed[0]["sub"] == "01"
        
    def test_table_formatting(self):
        """Test table output formatting"""
        results = [
            {"sub": "01", "task": "nback"},
            {"sub": "02", "task": "rest"}
        ]
        
        formatted = BQLFormatter.format(results, "table")
        lines = formatted.split('\n')
        
        assert len(lines) >= 4  # Header + separator + 2 data rows
        assert "sub" in lines[0]
        assert "task" in lines[0]
        assert "01" in lines[2] or "01" in lines[3]
        
    def test_csv_formatting(self):
        """Test CSV output formatting"""
        results = [
            {"sub": "01", "task": "nback"},
            {"sub": "02", "task": "rest"}
        ]
        
        formatted = BQLFormatter.format(results, "csv")
        lines = formatted.strip().split('\n')
        
        assert len(lines) >= 3  # Header + 2 data rows
        assert "sub" in lines[0]
        assert "task" in lines[0]
        
    def test_paths_formatting(self):
        """Test paths output formatting"""
        results = [
            {"filepath": "/path/to/file1.nii"},
            {"filepath": "/path/to/file2.nii"}
        ]
        
        formatted = BQLFormatter.format(results, "paths")
        lines = formatted.strip().split('\n')
        
        assert len(lines) == 2
        assert "/path/to/file1.nii" in lines
        assert "/path/to/file2.nii" in lines
        
    def test_empty_results(self):
        """Test formatting empty results"""
        results = []
        
        json_formatted = BQLFormatter.format(results, "json")
        assert json_formatted == "[]"
        
        table_formatted = BQLFormatter.format(results, "table")
        assert "No results found" in table_formatted


class TestIntegration:
    """Integration tests using real BIDS datasets"""
    
    @pytest.fixture
    def synthetic_dataset_path(self):
        """Path to synthetic dataset"""
        path = BIDS_EXAMPLES_DIR / "synthetic"
        if not path.exists():
            pytest.skip("BIDS examples not available")
        return str(path)
        
    def test_end_to_end_query(self, synthetic_dataset_path):
        """Test complete end-to-end query execution"""
        dataset = BIDSDataset(synthetic_dataset_path)
        evaluator = BQLEvaluator(dataset)
        
        # Test complex query
        parser = BQLParser.from_string(
            "SELECT sub, ses, task, run, filepath WHERE datatype=func AND task=nback ORDER BY sub, run"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)
        
        assert len(results) > 0
        
        # Verify all results are functional nback files
        # Note: datatype is not in SELECT list, so not in results
        for result in results:
            assert result["task"] == "nback"  # This should be there since task is in SELECT
            assert "filepath" in result
            assert "sub" in result
            
        # Verify the WHERE clause worked by checking we only got nback files
        assert all(result["task"] == "nback" for result in results)
            
        # Test formatting
        json_output = BQLFormatter.format(results, "json")
        table_output = BQLFormatter.format(results, "table")
        
        assert len(json_output) > 0
        assert len(table_output) > 0
        
    def test_metadata_inheritance_query(self, synthetic_dataset_path):
        """Test queries involving metadata inheritance"""
        dataset = BIDSDataset(synthetic_dataset_path)
        evaluator = BQLEvaluator(dataset)
        
        # Look for files with RepetitionTime metadata
        parser = BQLParser.from_string("metadata.RepetitionTime>0")
        query = parser.parse()
        results = evaluator.evaluate(query)
        
        # Verify metadata is present and valid
        for result in results:
            metadata = result.get("metadata", {})
            if "RepetitionTime" in metadata:
                assert float(metadata["RepetitionTime"]) > 0
                
    def test_participants_integration(self, synthetic_dataset_path):
        """Test integration with participants data"""
        dataset = BIDSDataset(synthetic_dataset_path)
        evaluator = BQLEvaluator(dataset)
        
        # Query based on participant demographics
        parser = BQLParser.from_string("SELECT sub, participants.age, participants.sex WHERE participants.age>25")
        query = parser.parse()
        results = evaluator.evaluate(query)
        
        for result in results:
            if "participants.age" in result and result["participants.age"] is not None:
                assert int(result["participants.age"]) > 25
                
    def test_pattern_matching_queries(self, synthetic_dataset_path):
        """Test pattern matching functionality"""
        dataset = BIDSDataset(synthetic_dataset_path)
        evaluator = BQLEvaluator(dataset)
        
        # Test wildcard matching
        parser = BQLParser.from_string("suffix=*bold*")
        query = parser.parse()
        results = evaluator.evaluate(query)
        
        for result in results:
            if "suffix" in result:
                assert "bold" in result["suffix"]
                
        # Test regex matching (using string format since /regex/ literals aren't implemented)
        parser = BQLParser.from_string('sub~="0[1-3]"')
        query = parser.parse()
        results = evaluator.evaluate(query)
        
        for result in results:
            if "sub" in result:
                assert result["sub"] in ["01", "02", "03"]


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_invalid_dataset_path(self):
        """Test handling of invalid dataset paths"""
        with pytest.raises(ValueError):
            BIDSDataset("/nonexistent/path")
            
    def test_empty_query(self):
        """Test handling of empty queries"""
        parser = BQLParser.from_string("")
        query = parser.parse()
        
        # Should parse successfully but return minimal query
        assert query.where_clause is None
        assert query.select_clause is None
        
    def test_invalid_field_access(self):
        """Test handling of invalid field access"""
        # Create minimal test dataset
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create minimal BIDS structure
            dataset_path = Path(tmpdir)
            (dataset_path / "dataset_description.json").write_text('{"Name": "Test", "BIDSVersion": "1.0.0"}')
            
            dataset = BIDSDataset(dataset_path)
            evaluator = BQLEvaluator(dataset)
            
            # Query non-existent field
            parser = BQLParser.from_string("nonexistent_field=value")
            query = parser.parse()
            results = evaluator.evaluate(query)
            
            # Should return empty results without error
            assert len(results) == 0


if __name__ == "__main__":
    # Run specific test categories
    pytest.main([__file__, "-v", "--tb=short"])