"""
Comprehensive tests for BIDS Query Language (BIQL)

Tests all components of the BIQL implementation using real BIDS examples.
"""

import json
import tempfile
from pathlib import Path

import pytest

from biql.dataset import BIDSDataset
from biql.evaluator import BIQLEvaluator
from biql.formatter import BIQLFormatter
from biql.lexer import BIQLLexer, TokenType
from biql.parser import BIQLParseError, BIQLParser

# Test constants
BIDS_EXAMPLES_DIR = Path("/home/ashley/repos/bids-examples/")


class TestBIQLLexer:
    """Test the BIQL lexer functionality"""

    def test_basic_tokenization(self):
        """Test basic token recognition"""
        lexer = BIQLLexer("sub=01 AND task=rest")
        tokens = lexer.tokenize()

        token_types = [t.type for t in tokens if t.type != TokenType.EOF]
        expected = [
            TokenType.IDENTIFIER,
            TokenType.EQ,
            TokenType.NUMBER,
            TokenType.AND,
            TokenType.IDENTIFIER,
            TokenType.EQ,
            TokenType.IDENTIFIER,
        ]
        assert token_types == expected

    def test_string_literals(self):
        """Test string literal tokenization"""
        lexer = BIQLLexer('task="n-back" OR suffix="T1w"')
        tokens = lexer.tokenize()

        string_tokens = [t for t in tokens if t.type == TokenType.STRING]
        assert len(string_tokens) == 2
        assert string_tokens[0].value == "n-back"
        assert string_tokens[1].value == "T1w"

    def test_operators(self):
        """Test operator tokenization"""
        lexer = BIQLLexer("metadata.RepetitionTime>=2.0 AND run<=[1:3]")
        tokens = lexer.tokenize()

        operator_tokens = [
            t for t in tokens if t.type in [TokenType.GTE, TokenType.LTE]
        ]
        assert len(operator_tokens) == 2

    def test_complex_query(self):
        """Test complex query tokenization"""
        query = (
            "SELECT sub, ses, filepath WHERE (task=nback OR task=rest) "
            "AND metadata.RepetitionTime<3.0"
        )
        lexer = BIQLLexer(query)
        tokens = lexer.tokenize()

        assert any(t.type == TokenType.SELECT for t in tokens)
        assert any(t.type == TokenType.WHERE for t in tokens)
        assert any(t.type == TokenType.LPAREN for t in tokens)
        assert any(t.type == TokenType.RPAREN for t in tokens)


class TestBIQLParser:
    """Test the BIQL parser functionality"""

    def test_simple_query_parsing(self):
        """Test parsing simple queries"""
        parser = BIQLParser.from_string("sub=01")
        query = parser.parse()

        assert query.where_clause is not None
        assert query.select_clause is None

    def test_select_query_parsing(self):
        """Test parsing SELECT queries"""
        parser = BIQLParser.from_string(
            "SELECT sub, task, filepath WHERE datatype=func"
        )
        query = parser.parse()

        assert query.select_clause is not None
        assert len(query.select_clause.items) == 3
        assert query.where_clause is not None

    def test_complex_where_clause(self):
        """Test parsing complex WHERE clauses"""
        parser = BIQLParser.from_string("(sub=01 OR sub=02) AND task=nback")
        query = parser.parse()

        assert query.where_clause is not None

    def test_group_by_parsing(self):
        """Test parsing GROUP BY clauses"""
        parser = BIQLParser.from_string("SELECT sub, COUNT(*) GROUP BY sub")
        query = parser.parse()

        assert query.group_by is not None
        assert "sub" in query.group_by

    def test_order_by_parsing(self):
        """Test parsing ORDER BY clauses"""
        parser = BIQLParser.from_string("sub=01 ORDER BY run DESC")
        query = parser.parse()

        assert query.order_by is not None
        assert query.order_by[0] == ("run", "DESC")

    def test_format_parsing(self):
        """Test parsing FORMAT clauses"""
        parser = BIQLParser.from_string("sub=01 FORMAT table")
        query = parser.parse()

        assert query.format == "table"

    def test_invalid_syntax(self):
        """Test that invalid syntax raises errors"""
        with pytest.raises(BIQLParseError):
            parser = BIQLParser.from_string("SELECT FROM WHERE")
            parser.parse()

    def test_distinct_parsing(self):
        """Test parsing SELECT DISTINCT queries"""
        parser = BIQLParser.from_string("SELECT DISTINCT sub, task")
        query = parser.parse()

        assert query.select_clause is not None
        assert query.select_clause.distinct is True
        assert len(query.select_clause.items) == 2
        assert query.select_clause.items[0] == ("sub", None)
        assert query.select_clause.items[1] == ("task", None)

    def test_non_distinct_parsing(self):
        """Test that regular SELECT queries have distinct=False"""
        parser = BIQLParser.from_string("SELECT sub, task")
        query = parser.parse()

        assert query.select_clause is not None
        assert query.select_clause.distinct is False

    def test_having_clause_parsing(self):
        """Test parsing HAVING clauses"""
        parser = BIQLParser.from_string(
            "SELECT sub, COUNT(*) GROUP BY sub HAVING COUNT(*) > 2"
        )
        query = parser.parse()

        assert query.group_by is not None
        assert query.having is not None

    def test_function_call_parsing_with_arguments(self):
        """Test parsing function calls with different argument types"""
        # Function with STAR argument
        parser = BIQLParser.from_string("SELECT COUNT(*)")
        query = parser.parse()

        assert query.select_clause is not None
        assert len(query.select_clause.items) == 1
        assert query.select_clause.items[0][0] == "COUNT(*)"

        # Function with field argument
        parser = BIQLParser.from_string("SELECT AVG(metadata.RepetitionTime)")
        query = parser.parse()

        assert query.select_clause is not None
        assert len(query.select_clause.items) == 1
        # Should parse as AVG(metadata.RepetitionTime)
        assert "AVG" in query.select_clause.items[0][0]

    def test_not_operator_parsing(self):
        """Test parsing NOT operator"""
        parser = BIQLParser.from_string("NOT datatype=func")
        query = parser.parse()

        assert query.where_clause is not None
        # Should parse successfully

    def test_complex_function_calls_in_select(self):
        """Test function calls in SELECT with aliases"""
        parser = BIQLParser.from_string("SELECT COUNT(*) AS total_files, sub")
        query = parser.parse()

        assert query.select_clause is not None
        assert len(query.select_clause.items) == 2
        assert query.select_clause.items[0] == ("COUNT(*)", "total_files")
        assert query.select_clause.items[1] == ("sub", None)

    def test_list_expression_parsing(self):
        """Test parsing list expressions in IN clauses"""
        parser = BIQLParser.from_string("sub IN [01, 02, 03]")
        query = parser.parse()

        assert query.where_clause is not None
        # Should parse without errors

    def test_wildcard_pattern_parsing_edge_cases(self):
        """Test wildcard pattern parsing with mixed patterns"""
        # Test identifier followed by wildcard
        parser = BIQLParser.from_string("suffix=bold*")
        query = parser.parse()

        assert query.where_clause is not None

        # Test pattern with question marks
        parser = BIQLParser.from_string("suffix=T?w")
        query = parser.parse()

        assert query.where_clause is not None

    def test_multiple_comma_separated_items(self):
        """Test parsing multiple comma-separated items in various contexts"""
        # Multiple ORDER BY fields
        parser = BIQLParser.from_string("sub=01 ORDER BY sub ASC, ses DESC, run ASC")
        query = parser.parse()

        assert query.order_by is not None
        assert len(query.order_by) == 3
        assert query.order_by[0] == ("sub", "ASC")
        assert query.order_by[1] == ("ses", "DESC")
        assert query.order_by[2] == ("run", "ASC")

        # Multiple GROUP BY fields
        parser = BIQLParser.from_string("SELECT COUNT(*) GROUP BY sub, ses, datatype")
        query = parser.parse()

        assert query.group_by is not None
        assert len(query.group_by) == 3
        assert "sub" in query.group_by
        assert "ses" in query.group_by
        assert "datatype" in query.group_by


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
        func_files = [
            f for f in synthetic_dataset.files if f.entities.get("datatype") == "func"
        ]
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


class TestBIQLEvaluator:
    """Test BIQL query evaluation"""

    @pytest.fixture
    def synthetic_dataset(self):
        """Fixture for synthetic BIDS dataset"""
        if not (BIDS_EXAMPLES_DIR / "synthetic").exists():
            pytest.skip("BIDS examples not available")
        return BIDSDataset(BIDS_EXAMPLES_DIR / "synthetic")

    @pytest.fixture
    def evaluator(self, synthetic_dataset):
        """Fixture for BIQL evaluator"""
        return BIQLEvaluator(synthetic_dataset)

    def test_simple_entity_query(self, evaluator):
        """Test simple entity-based queries"""
        parser = BIQLParser.from_string("sub=01")
        query = parser.parse()
        results = evaluator.evaluate(query)

        assert len(results) > 0
        for result in results:
            assert result["sub"] == "01"

    def test_datatype_filtering(self, evaluator):
        """Test datatype filtering"""
        parser = BIQLParser.from_string("datatype=func")
        query = parser.parse()
        results = evaluator.evaluate(query)

        assert len(results) > 0
        for result in results:
            assert result["datatype"] == "func"

    def test_task_filtering(self, evaluator):
        """Test task filtering"""
        parser = BIQLParser.from_string("task=nback")
        query = parser.parse()
        results = evaluator.evaluate(query)

        assert len(results) > 0
        for result in results:
            assert result["task"] == "nback"

    def test_logical_operators(self, evaluator):
        """Test logical AND/OR operators"""
        parser = BIQLParser.from_string("sub=01 AND datatype=func")
        query = parser.parse()
        results = evaluator.evaluate(query)

        for result in results:
            assert result["sub"] == "01"
            assert result["datatype"] == "func"

        parser = BIQLParser.from_string("task=nback OR task=rest")
        query = parser.parse()
        results = evaluator.evaluate(query)

        for result in results:
            assert result["task"] in ["nback", "rest"]

    def test_range_queries(self, evaluator):
        """Test range queries"""
        parser = BIQLParser.from_string("run=[1:2]")
        query = parser.parse()
        results = evaluator.evaluate(query)

        for result in results:
            if "run" in result:
                run_val = int(result["run"])
                assert 1 <= run_val <= 2

    def test_wildcard_matching(self, evaluator):
        """Test wildcard pattern matching"""
        parser = BIQLParser.from_string("suffix=*bold*")
        query = parser.parse()
        results = evaluator.evaluate(query)

        for result in results:
            if "suffix" in result:
                assert "bold" in result["suffix"]

    def test_metadata_queries(self, evaluator):
        """Test metadata queries"""
        parser = BIQLParser.from_string("metadata.RepetitionTime>0")
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
        parser = BIQLParser.from_string("participants.age>20")
        query = parser.parse()
        results = evaluator.evaluate(query)

        for result in results:
            participants = result.get("participants", {})
            if "age" in participants:
                assert int(participants["age"]) > 20

    def test_select_clause(self, evaluator):
        """Test SELECT clause functionality"""
        parser = BIQLParser.from_string(
            "SELECT sub, task, filepath WHERE datatype=func"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)

        if results:
            result = results[0]
            expected_keys = {"sub", "task", "filepath"}
            # Result may have more keys, but should have at least these
            assert expected_keys.issubset(set(result.keys()))

    def test_group_by_functionality(self, evaluator):
        """Test GROUP BY functionality"""
        parser = BIQLParser.from_string("SELECT sub, COUNT(*) GROUP BY sub")
        query = parser.parse()
        results = evaluator.evaluate(query)

        assert len(results) > 0
        for result in results:
            assert "sub" in result
            assert "count" in result
            assert result["count"] > 0

    def test_order_by_functionality(self, evaluator):
        """Test ORDER BY functionality"""
        parser = BIQLParser.from_string("datatype=func ORDER BY sub ASC")
        query = parser.parse()
        results = evaluator.evaluate(query)

        if len(results) > 1:
            # Check that results are ordered by subject
            subjects = [r.get("sub", "") for r in results]
            assert subjects == sorted(subjects)

    def test_group_by_auto_aggregation(self, evaluator):
        """Test auto-aggregation of non-grouped fields in GROUP BY queries"""
        parser = BIQLParser.from_string(
            "SELECT sub, task, filepath, COUNT(*) WHERE datatype=func GROUP BY sub"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)

        if len(results) > 0:
            result = results[0]

            # Grouped field should be a single value
            assert "sub" in result
            assert isinstance(result["sub"], str)

            # Non-grouped fields should be aggregated into arrays when needed
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
        parser = BIQLParser.from_string(
            "SELECT sub, datatype, COUNT(*) WHERE datatype=func GROUP BY sub, datatype"
        )
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
        parser = BIQLParser.from_string("SELECT sub, datatype, COUNT(*) GROUP BY sub")
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
        parser = BIQLParser.from_string("SELECT sub, run, COUNT(*) GROUP BY sub")
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
        parser = BIQLParser.from_string("SELECT datatype")
        query = parser.parse()
        regular_results = evaluator.evaluate(query)

        # Now get DISTINCT results
        parser = BIQLParser.from_string("SELECT DISTINCT datatype")
        query = parser.parse()
        distinct_results = evaluator.evaluate(query)

        # DISTINCT should have fewer or equal results
        assert len(distinct_results) <= len(regular_results)

        # All results should be unique
        seen_datatypes = set()
        for result in distinct_results:
            datatype = result.get("datatype")
            assert (
                datatype not in seen_datatypes
            ), f"Duplicate datatype found: {datatype}"
            seen_datatypes.add(datatype)

    def test_distinct_multiple_fields(self, evaluator):
        """Test DISTINCT with multiple fields"""
        parser = BIQLParser.from_string("SELECT DISTINCT sub, datatype")
        query = parser.parse()
        results = evaluator.evaluate(query)

        # Check that all combinations are unique
        seen_combinations = set()
        for result in results:
            combination = (result.get("sub"), result.get("datatype"))
            assert (
                combination not in seen_combinations
            ), f"Duplicate combination: {combination}"
            seen_combinations.add(combination)

    def test_distinct_with_where_clause(self, evaluator):
        """Test DISTINCT combined with WHERE clause"""
        parser = BIQLParser.from_string("SELECT DISTINCT task WHERE datatype=func")
        query = parser.parse()
        results = evaluator.evaluate(query)

        # Should only have unique task values from functional files
        seen_tasks = set()
        for result in results:
            task = result.get("task")
            if task is not None:
                assert task not in seen_tasks, f"Duplicate task found: {task}"
                seen_tasks.add(task)

    def test_having_clause_functionality(self, evaluator):
        """Test HAVING clause with aggregate functions"""
        parser = BIQLParser.from_string(
            "SELECT sub, COUNT(*) GROUP BY sub HAVING COUNT(*) > 2"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)

        # All results should have count > 2
        for result in results:
            count = result.get("count", 0)
            assert count > 2, f"HAVING clause failed: count={count} should be > 2"

    def test_having_clause_different_operators(self, evaluator):
        """Test HAVING clause with different comparison operators"""
        # Test >= operator
        parser = BIQLParser.from_string(
            "SELECT datatype, COUNT(*) GROUP BY datatype HAVING COUNT(*) >= 1"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)

        for result in results:
            count = result.get("count", 0)
            assert count >= 1

        # Test < operator (should return empty for reasonable datasets)
        parser = BIQLParser.from_string(
            "SELECT sub, COUNT(*) GROUP BY sub HAVING COUNT(*) < 1"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)
        # Should be empty since no subject can have < 1 files
        assert len(results) == 0

    def test_error_handling_invalid_field_comparison(self, evaluator):
        """Test error handling for invalid field comparisons"""
        # This should not crash, just return no results for non-existent fields
        parser = BIQLParser.from_string("nonexistent_field=value")
        query = parser.parse()
        results = evaluator.evaluate(query)
        assert len(results) == 0

    def test_error_handling_type_conversion(self, evaluator):
        """Test error handling for type conversion in comparisons"""
        # Test numeric comparison with non-numeric string (falls back to string)
        parser = BIQLParser.from_string("sub>999")  # sub is usually a string like "01"
        query = parser.parse()
        results = evaluator.evaluate(query)
        # Should not crash, may return results based on string comparison
        assert isinstance(results, list)

    def test_not_operator(self, evaluator):
        """Test NOT operator functionality"""
        parser = BIQLParser.from_string("NOT datatype=func")
        query = parser.parse()
        results = evaluator.evaluate(query)

        # Should only return non-functional files
        for result in results:
            datatype = result.get("datatype")
            assert datatype != "func" or datatype is None

    def test_in_operator_with_lists(self, evaluator):
        """Test IN operator with list values"""
        parser = BIQLParser.from_string("sub IN [01, 02, 03]")
        query = parser.parse()
        results = evaluator.evaluate(query)

        for result in results:
            sub = result.get("sub")
            if sub is not None:
                assert sub in ["01", "02", "03"]

    def test_like_operator(self, evaluator):
        """Test LIKE operator for SQL-style pattern matching"""
        parser = BIQLParser.from_string("task LIKE %back%")
        query = parser.parse()
        results = evaluator.evaluate(query)

        for result in results:
            task = result.get("task")
            if task is not None:
                assert "back" in task

    def test_regex_match_operator(self, evaluator):
        """Test regex MATCH operator (~=)"""
        parser = BIQLParser.from_string('sub~="0[1-3]"')
        query = parser.parse()
        results = evaluator.evaluate(query)

        for result in results:
            sub = result.get("sub")
            if sub is not None:
                assert sub in ["01", "02", "03"]

    def test_range_queries_edge_cases(self, evaluator):
        """Test range queries with edge cases"""
        # Test range with string values that can be converted to numbers
        parser = BIQLParser.from_string("run=[1:3]")
        query = parser.parse()
        results = evaluator.evaluate(query)

        for result in results:
            run = result.get("run")
            if run is not None:
                try:
                    run_num = int(run)
                    assert 1 <= run_num <= 3
                except ValueError:
                    # If run can't be converted to int, the range shouldn't match
                    pass

    def test_metadata_field_access_edge_cases(self, evaluator):
        """Test metadata field access with missing values"""
        # Test accessing nested metadata that doesn't exist
        parser = BIQLParser.from_string("metadata.NonExistentField=value")
        query = parser.parse()
        results = evaluator.evaluate(query)

        # Should return empty results without crashing
        assert len(results) == 0

    def test_participants_field_access_edge_cases(self, evaluator):
        """Test participants data access with missing values"""
        # Test accessing participant data for non-existent field
        parser = BIQLParser.from_string("participants.nonexistent=value")
        query = parser.parse()
        results = evaluator.evaluate(query)

        # Should not crash, may return empty results
        assert isinstance(results, list)


class TestQSMWorkflow:
    """Test QSM-specific workflow scenarios"""

    def test_qsm_reconstruction_groups_with_filenames(self):
        """Test QSM reconstruction groups include filename arrays (real QSM use case)"""
        # Create a minimal test dataset with QSM-like structure
        import json
        import tempfile
        from pathlib import Path

        from biql.dataset import BIDSDataset
        from biql.evaluator import BIQLEvaluator
        from biql.parser import BIQLParser

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
                "sub-02/anat/sub-02_acq-test_echo-01_part-phase_MEGRE.nii",
            ]

            for file_path in qsm_files:
                full_path = tmpdir / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.touch()

            # Test the QSM reconstruction grouping query
            dataset = BIDSDataset(tmpdir)
            evaluator = BIQLEvaluator(dataset)

            parser = BIQLParser.from_string(
                "SELECT filename, sub, acq, part, echo, COUNT(*) "
                "WHERE (part=mag OR part=phase) AND suffix=MEGRE "
                "GROUP BY sub, acq"
            )
            query = parser.parse()
            results = evaluator.evaluate(query)

            assert (
                len(results) == 2
            )  # Two groups: sub-01 (no acq) and sub-02 (acq-test)

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
            sub01_group = next(
                r for r in results if r["sub"] == "01" and r.get("acq") is None
            )
            assert sub01_group["count"] == 4  # 2 echoes × 2 parts

            # Verify subject 02 group (with acquisition)
            sub02_group = next(
                r for r in results if r["sub"] == "02" and r.get("acq") == "test"
            )
            assert sub02_group["count"] == 2  # 1 echo × 2 parts

    def test_distinct_echo_times_discovery(self):
        """Test DISTINCT for discovering unique EchoTime values (real QSM use case)"""
        # Create test dataset with varying echo times
        import json
        import tempfile
        from pathlib import Path

        from biql.dataset import BIDSDataset
        from biql.evaluator import BIQLEvaluator
        from biql.parser import BIQLParser

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
                (
                    "sub-02/anat/sub-02_echo-01_part-mag_MEGRE.nii",
                    0.005,
                ),  # Same as sub-01
                ("sub-02/anat/sub-02_echo-01_part-mag_MEGRE.json", 0.005),
                ("sub-02/anat/sub-02_echo-02_part-mag_MEGRE.nii", 0.015),  # Different
                ("sub-02/anat/sub-02_echo-02_part-mag_MEGRE.json", 0.015),
            ]

            for file_path, echo_time in echo_files:
                full_path = tmpdir / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)

                if file_path.endswith(".json"):
                    metadata = {"EchoTime": echo_time, "MagneticFieldStrength": 3.0}
                    full_path.write_text(json.dumps(metadata))
                else:
                    full_path.touch()

            # Test DISTINCT metadata.EchoTime
            dataset = BIDSDataset(tmpdir)
            evaluator = BIQLEvaluator(dataset)

            parser = BIQLParser.from_string(
                "SELECT DISTINCT metadata.EchoTime WHERE suffix=MEGRE"
            )
            query = parser.parse()
            results = evaluator.evaluate(query)

            # Should have 3 unique echo times: 0.005, 0.010, 0.015
            echo_times = [
                r.get("metadata.EchoTime")
                for r in results
                if r.get("metadata.EchoTime") is not None
            ]
            assert len(echo_times) == 3
            assert 0.005 in echo_times
            assert 0.010 in echo_times
            assert 0.015 in echo_times

            # Test DISTINCT echo (should be 01, 02)
            parser = BIQLParser.from_string("SELECT DISTINCT echo WHERE suffix=MEGRE")
            query = parser.parse()
            results = evaluator.evaluate(query)

            echo_numbers = [r.get("echo") for r in results if r.get("echo") is not None]
            assert len(echo_numbers) == 2
            assert "01" in echo_numbers
            assert "02" in echo_numbers


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
        assert isinstance(paths_formatted, str)


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
        evaluator = BIQLEvaluator(dataset)

        # Test complex query
        parser = BIQLParser.from_string(
            "SELECT sub, ses, task, run, filepath "
            "WHERE datatype=func AND task=nback ORDER BY sub, run"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)

        assert len(results) > 0

        # Verify all results are functional nback files
        # Note: datatype is not in SELECT list, so not in results
        for result in results:
            assert (
                result["task"] == "nback"
            )  # This should be there since task is in SELECT
            assert "filepath" in result
            assert "sub" in result

        # Verify the WHERE clause worked by checking we only got nback files
        assert all(result["task"] == "nback" for result in results)

        # Test formatting
        json_output = BIQLFormatter.format(results, "json")
        table_output = BIQLFormatter.format(results, "table")

        assert len(json_output) > 0
        assert len(table_output) > 0

    def test_metadata_inheritance_query(self, synthetic_dataset_path):
        """Test queries involving metadata inheritance"""
        dataset = BIDSDataset(synthetic_dataset_path)
        evaluator = BIQLEvaluator(dataset)

        # Look for files with RepetitionTime metadata
        parser = BIQLParser.from_string("metadata.RepetitionTime>0")
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
        evaluator = BIQLEvaluator(dataset)

        # Query based on participant demographics
        parser = BIQLParser.from_string(
            "SELECT sub, participants.age, participants.sex WHERE participants.age>25"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)

        for result in results:
            if "participants.age" in result and result["participants.age"] is not None:
                assert int(result["participants.age"]) > 25

    def test_pattern_matching_queries(self, synthetic_dataset_path):
        """Test pattern matching functionality"""
        dataset = BIDSDataset(synthetic_dataset_path)
        evaluator = BIQLEvaluator(dataset)

        # Test wildcard matching
        parser = BIQLParser.from_string("suffix=*bold*")
        query = parser.parse()
        results = evaluator.evaluate(query)

        for result in results:
            if "suffix" in result:
                assert "bold" in result["suffix"]

        # Test regex matching (using string format since /regex/ not implemented)
        parser = BIQLParser.from_string('sub~="0[1-3]"')
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
        parser = BIQLParser.from_string("")
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
            (dataset_path / "dataset_description.json").write_text(
                '{"Name": "Test", "BIDSVersion": "1.0.0"}'
            )

            dataset = BIDSDataset(dataset_path)
            evaluator = BIQLEvaluator(dataset)

            # Query non-existent field
            parser = BIQLParser.from_string("nonexistent_field=value")
            query = parser.parse()
            results = evaluator.evaluate(query)

            # Should return empty results without error
            assert len(results) == 0


if __name__ == "__main__":
    # Run specific test categories
    pytest.main([__file__, "-v", "--tb=short"])
