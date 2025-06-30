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

    def test_array_agg_parsing(self):
        """Test parsing of ARRAY_AGG functions"""
        # Test basic ARRAY_AGG
        parser = BIQLParser.from_string("SELECT ARRAY_AGG(filename)")
        query = parser.parse()

        assert query.select_clause is not None
        assert len(query.select_clause.items) == 1
        assert query.select_clause.items[0][0] == "ARRAY_AGG(filename)"

        # Test ARRAY_AGG with WHERE condition
        parser = BIQLParser.from_string("SELECT ARRAY_AGG(filename WHERE part='mag')")
        query = parser.parse()

        assert query.select_clause is not None
        assert len(query.select_clause.items) == 1
        assert (
            "ARRAY_AGG(filename WHERE part = 'mag')" in query.select_clause.items[0][0]
        )

        # Test ARRAY_AGG with alias
        parser = BIQLParser.from_string(
            "SELECT ARRAY_AGG(filename WHERE part='phase') AS phase_files"
        )
        query = parser.parse()

        assert query.select_clause is not None
        assert len(query.select_clause.items) == 1
        assert query.select_clause.items[0][1] == "phase_files"

        # Test multiple ARRAY_AGG functions
        parser = BIQLParser.from_string(
            "SELECT ARRAY_AGG(filename WHERE part='mag') AS mag_files, "
            "ARRAY_AGG(filename WHERE part='phase') AS phase_files"
        )
        query = parser.parse()

        assert query.select_clause is not None
        assert len(query.select_clause.items) == 2
        assert query.select_clause.items[0][1] == "mag_files"
        assert query.select_clause.items[1][1] == "phase_files"


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

    def test_aggregate_functions(self, evaluator):
        """Test all aggregate functions: AVG, MAX, MIN, SUM"""
        # Test AVG function
        parser = BIQLParser.from_string("SELECT datatype, AVG(run) GROUP BY datatype")
        query = parser.parse()
        results = evaluator.evaluate(query)
        if results:
            for result in results:
                assert "datatype" in result
                if "avg" in result and result["avg"] is not None:
                    assert isinstance(result["avg"], (int, float))

        # Test MAX function
        parser = BIQLParser.from_string("SELECT datatype, MAX(run) GROUP BY datatype")
        query = parser.parse()
        results = evaluator.evaluate(query)
        if results:
            for result in results:
                assert "datatype" in result
                if "max" in result and result["max"] is not None:
                    assert isinstance(result["max"], (int, float))

        # Test MIN function
        parser = BIQLParser.from_string("SELECT datatype, MIN(run) GROUP BY datatype")
        query = parser.parse()
        results = evaluator.evaluate(query)
        if results:
            for result in results:
                assert "datatype" in result
                if "min" in result and result["min"] is not None:
                    assert isinstance(result["min"], (int, float))

        # Test SUM function
        parser = BIQLParser.from_string("SELECT datatype, SUM(run) GROUP BY datatype")
        query = parser.parse()
        results = evaluator.evaluate(query)
        if results:
            for result in results:
                assert "datatype" in result
                if "sum" in result and result["sum"] is not None:
                    assert isinstance(result["sum"], (int, float))

        # Test multiple aggregate functions together
        parser = BIQLParser.from_string(
            "SELECT datatype, COUNT(*), AVG(run), MAX(run), MIN(run), SUM(run) GROUP BY datatype"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)

        if results:
            for result in results:
                assert "datatype" in result
                assert "count" in result
                assert isinstance(result["count"], int)
                # Other aggregates may be None if no run values exist
                for agg in ["avg", "max", "min", "sum"]:
                    if agg in result and result[agg] is not None:
                        assert isinstance(result[agg], (int, float))

        # Test with aliases
        parser = BIQLParser.from_string(
            "SELECT datatype, AVG(run) AS average_run, MAX(run) AS max_run GROUP BY datatype"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)

        if results:
            for result in results:
                assert "datatype" in result
                # Check aliases are used
                if "average_run" in result:
                    assert "avg" not in result
                if "max_run" in result:
                    assert "max" not in result

    def test_array_agg_functionality(self, evaluator):
        """Test ARRAY_AGG function with and without WHERE conditions"""
        # Test basic ARRAY_AGG without WHERE
        parser = BIQLParser.from_string(
            "SELECT datatype, ARRAY_AGG(filename) GROUP BY datatype"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)

        if results:
            for result in results:
                assert "datatype" in result
                assert "array_agg" in result
                assert isinstance(result["array_agg"], list)

        # Test ARRAY_AGG with WHERE condition
        parser = BIQLParser.from_string(
            "SELECT datatype, ARRAY_AGG(filename WHERE part='mag') AS mag_files GROUP BY datatype"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)

        if results:
            for result in results:
                assert "datatype" in result
                assert "mag_files" in result
                assert isinstance(result["mag_files"], list)
                # All files in mag_files should contain 'mag' in their name
                for filename in result["mag_files"]:
                    assert "mag" in filename.lower()

        # Test ARRAY_AGG with different WHERE conditions
        parser = BIQLParser.from_string(
            "SELECT sub, ARRAY_AGG(filename WHERE datatype='func') AS func_files GROUP BY sub"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)

        if results:
            for result in results:
                assert "sub" in result
                assert "func_files" in result
                assert isinstance(result["func_files"], list)

        # Test multiple ARRAY_AGG functions with different conditions
        parser = BIQLParser.from_string(
            "SELECT sub, ARRAY_AGG(filename WHERE datatype='func') AS func_files, "
            "ARRAY_AGG(filename WHERE datatype='anat') AS anat_files GROUP BY sub"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)

        if results:
            for result in results:
                assert "sub" in result
                assert "func_files" in result
                assert "anat_files" in result
                assert isinstance(result["func_files"], list)
                assert isinstance(result["anat_files"], list)

        # Test the QSM use case - similar to user's example
        parser = BIQLParser.from_string(
            "SELECT sub, ses, acq, run, "
            "ARRAY_AGG(filename WHERE part='mag') AS mag_filenames, "
            "ARRAY_AGG(filename WHERE part='phase') AS phase_filenames "
            "WHERE (part='mag' OR part='phase') GROUP BY sub, ses, acq, run"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)

        # Verify structure - should work even if dataset doesn't have these specific files
        if results:
            for result in results:
                assert "sub" in result
                assert "ses" in result
                assert "acq" in result
                assert "run" in result
                assert "mag_filenames" in result
                assert "phase_filenames" in result
                assert isinstance(result["mag_filenames"], list)
                assert isinstance(result["phase_filenames"], list)

    def test_array_agg_edge_cases(self, evaluator):
        """Test edge cases for ARRAY_AGG functionality"""
        # Test ARRAY_AGG with non-existent field
        parser = BIQLParser.from_string(
            "SELECT ARRAY_AGG(nonexistent_field) AS missing GROUP BY datatype"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)

        if results:
            for result in results:
                assert "missing" in result
                # Should be empty list or list with None values filtered out
                assert isinstance(result["missing"], list)

        # Test ARRAY_AGG with WHERE condition that matches nothing
        parser = BIQLParser.from_string(
            "SELECT ARRAY_AGG(filename WHERE part='nonexistent') AS empty_files GROUP BY datatype"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)

        if results:
            for result in results:
                assert "empty_files" in result
                # Should be empty list when condition matches nothing
                assert result["empty_files"] == []

        # Test ARRAY_AGG without GROUP BY (single row)
        parser = BIQLParser.from_string(
            "SELECT ARRAY_AGG(filename WHERE datatype='func') AS func_files"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)

        # Should work and return arrays even without GROUP BY
        assert isinstance(results, list)
        if results:
            for result in results:
                if "func_files" in result:
                    assert isinstance(result["func_files"], list)

    def test_array_agg_condition_types(self, evaluator):
        """Test different types of WHERE conditions in ARRAY_AGG"""
        # Test equality condition
        parser = BIQLParser.from_string(
            "SELECT ARRAY_AGG(filename WHERE datatype='func') AS func_files GROUP BY sub"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)
        # Should parse and execute without error

        # Test inequality condition
        parser = BIQLParser.from_string(
            "SELECT ARRAY_AGG(filename WHERE datatype!='dwi') AS non_dwi_files GROUP BY sub"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)
        # Should parse and execute without error

        # Test with quoted values
        parser = BIQLParser.from_string(
            "SELECT ARRAY_AGG(filename WHERE suffix='bold') AS bold_files GROUP BY sub"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)
        # Should parse and execute without error

        # Test with numeric-like values
        parser = BIQLParser.from_string(
            "SELECT ARRAY_AGG(filename WHERE run='01') AS run01_files GROUP BY sub"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)
        # Should parse and execute without error

    def test_array_agg_complex_conditions(self, evaluator):
        """Test complex WHERE conditions with AND/OR in ARRAY_AGG"""
        # Test AND condition - should only return .nii files that are phase
        parser = BIQLParser.from_string(
            "SELECT ARRAY_AGG(filename WHERE part='phase' AND extension='.nii') AS phase_nii_files, ARRAY_AGG(filename WHERE part='phase') AS all_phase_files GROUP BY sub"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)

        # Verify parsing works and doesn't crash
        assert isinstance(results, list)

        # Check that the AND condition filters correctly
        for result in results:
            if "phase_nii_files" in result and "all_phase_files" in result:
                phase_nii = result["phase_nii_files"]
                all_phase = result["all_phase_files"]

                # phase_nii_files should be a subset of all_phase_files
                if phase_nii and all_phase:
                    assert isinstance(phase_nii, list)
                    assert isinstance(all_phase, list)
                    # All files in phase_nii should end with .nii
                    for filename in phase_nii:
                        assert filename.endswith(
                            ".nii"
                        ), f"Expected .nii file, got {filename}"
                    # phase_nii should have <= files than all_phase (since it's more restrictive)
                    assert len(phase_nii) <= len(all_phase)

        # Test OR condition
        parser = BIQLParser.from_string(
            "SELECT ARRAY_AGG(filename WHERE part='mag' OR part='phase') AS mag_or_phase_files GROUP BY sub"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)

        assert isinstance(results, list)

        # Test nested conditions with parentheses
        parser = BIQLParser.from_string(
            "SELECT ARRAY_AGG(filename WHERE (part='phase' AND extension='.nii') OR (part='mag' AND extension='.json')) AS mixed_files GROUP BY sub"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)

        assert isinstance(results, list)

    def test_array_agg_with_aliases(self, evaluator):
        """Test ARRAY_AGG with various alias configurations"""
        # Test single ARRAY_AGG with alias
        parser = BIQLParser.from_string(
            "SELECT ARRAY_AGG(filename WHERE part='mag') AS magnitude_files GROUP BY sub"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)

        if results:
            for result in results:
                assert "magnitude_files" in result
                assert "array_agg" not in result  # Should use alias, not default name
                assert isinstance(result["magnitude_files"], list)

        # Test multiple ARRAY_AGG with different aliases
        parser = BIQLParser.from_string(
            "SELECT sub, "
            "ARRAY_AGG(filename WHERE echo='1') AS echo1_files, "
            "ARRAY_AGG(filename WHERE echo='2') AS echo2_files "
            "GROUP BY sub"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)

        if results:
            for result in results:
                assert "sub" in result
                assert "echo1_files" in result
                assert "echo2_files" in result
                assert isinstance(result["echo1_files"], list)
                assert isinstance(result["echo2_files"], list)

    def test_format_clause_in_query(self, evaluator):
        """Test FORMAT clause within queries"""
        # Test with json format
        parser = BIQLParser.from_string(
            "SELECT sub, datatype WHERE datatype=func FORMAT json"
        )
        query = parser.parse()
        assert query.format == "json"

        # Test with table format
        parser = BIQLParser.from_string("sub=01 FORMAT table")
        query = parser.parse()
        assert query.format == "table"

        # Test with csv format
        parser = BIQLParser.from_string("SELECT * FORMAT csv")
        query = parser.parse()
        assert query.format == "csv"

        # Test with tsv format
        parser = BIQLParser.from_string(
            "SELECT filename, sub, datatype GROUP BY datatype FORMAT tsv"
        )
        query = parser.parse()
        assert query.format == "tsv"

        # Test with paths format
        parser = BIQLParser.from_string("datatype=anat FORMAT paths")
        query = parser.parse()
        assert query.format == "paths"

        # Test combined with all other clauses
        parser = BIQLParser.from_string(
            "SELECT sub, COUNT(*) WHERE datatype=func GROUP BY sub HAVING COUNT(*) > 1 ORDER BY sub DESC FORMAT json"
        )
        query = parser.parse()
        assert query.format == "json"
        assert query.select_clause is not None
        assert query.where_clause is not None
        assert query.group_by is not None
        assert query.having is not None
        assert query.order_by is not None

    def test_order_by_functionality(self, evaluator):
        """Test ORDER BY functionality"""
        parser = BIQLParser.from_string("datatype=func ORDER BY sub ASC")
        query = parser.parse()
        results = evaluator.evaluate(query)

        if len(results) > 1:
            # Check that results are ordered by subject
            subjects = [r.get("sub", "") for r in results]
            assert subjects == sorted(subjects)

    def test_complex_order_by_scenarios(self, evaluator):
        """Test complex ORDER BY scenarios"""
        # Note: ORDER BY aggregate functions not supported in current implementation

        # Test mixed ASC/DESC ordering
        parser = BIQLParser.from_string("ORDER BY datatype ASC, sub DESC")
        query = parser.parse()
        results = evaluator.evaluate(query)

        # Test ordering with NULL values
        parser = BIQLParser.from_string("SELECT sub, run ORDER BY run ASC")
        query = parser.parse()
        results = evaluator.evaluate(query)

        # Check that non-null values are sorted correctly
        non_null_runs = []
        for result in results:
            if result.get("run") is not None:
                non_null_runs.append(result["run"])

        # Convert to comparable types and verify sorting
        if non_null_runs:
            # Try to convert to int if possible for proper numeric sorting
            try:
                numeric_runs = [int(r) for r in non_null_runs]
                assert numeric_runs == sorted(numeric_runs)
            except ValueError:
                # Fall back to string comparison
                assert non_null_runs == sorted(non_null_runs)

        # Test ordering by multiple fields
        parser = BIQLParser.from_string("ORDER BY sub ASC, ses ASC, run ASC")
        query = parser.parse()
        results = evaluator.evaluate(query)

        # Verify complex ordering
        for i in range(1, len(results)):
            prev = results[i - 1]
            curr = results[i]

            # Primary sort by sub
            if prev.get("sub") and curr.get("sub"):
                if prev["sub"] < curr["sub"]:
                    continue
                elif prev["sub"] == curr["sub"]:
                    # Secondary sort by ses
                    if prev.get("ses") and curr.get("ses"):
                        if prev["ses"] < curr["ses"]:
                            continue
                        elif prev["ses"] == curr["ses"]:
                            # Tertiary sort by run
                            if prev.get("run") and curr.get("run"):
                                assert prev["run"] <= curr["run"]

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

    def test_field_existence_checks(self, evaluator):
        """Test field existence behavior with WHERE field syntax"""
        # Test basic entity existence check
        parser = BIQLParser.from_string("WHERE sub")
        query = parser.parse()
        results = evaluator.evaluate(query)

        # All results should have sub field (since it's a core BIDS entity)
        for result in results:
            assert "sub" in result
            assert result["sub"] is not None

        # Test metadata field existence
        parser = BIQLParser.from_string("WHERE metadata.RepetitionTime")
        query = parser.parse()
        results = evaluator.evaluate(query)

        # Only files with RepetitionTime metadata should be returned
        for result in results:
            if "metadata" in result and result["metadata"]:
                # If we have metadata, RepetitionTime should exist
                metadata = result["metadata"]
                if isinstance(metadata, dict):
                    assert "RepetitionTime" in metadata or len(results) == 0

        # Test with DISTINCT for entity discovery pattern
        parser = BIQLParser.from_string("SELECT DISTINCT task WHERE task")
        query = parser.parse()
        results = evaluator.evaluate(query)

        # All results should have non-null task values
        for result in results:
            assert "task" in result
            assert result["task"] is not None
            assert result["task"] != ""

        # Test non-existent field existence check
        parser = BIQLParser.from_string("WHERE nonexistent_field")
        query = parser.parse()
        results = evaluator.evaluate(query)

        # Should return empty results since field doesn't exist
        assert len(results) == 0

    def test_field_existence_vs_comparison(self, evaluator):
        """Test difference between field existence (WHERE field) and null comparison"""
        # Get baseline - all files
        parser = BIQLParser.from_string("SELECT filename")
        query = parser.parse()
        all_results = evaluator.evaluate(query)

        # Test field existence filter with field included in SELECT
        parser = BIQLParser.from_string("SELECT filename, run WHERE run")
        query = parser.parse()
        existence_results = evaluator.evaluate(query)

        # Existence check should return subset of all results
        assert len(existence_results) <= len(all_results)

        # All existence results should have run field with non-null values
        for result in existence_results:
            assert "run" in result
            assert result["run"] is not None

        # Test with just WHERE clause (no SELECT) - should include all fields
        parser = BIQLParser.from_string("WHERE run")
        query = parser.parse()
        no_select_results = evaluator.evaluate(query)

        # Should include run field and it should be non-null
        for result in no_select_results:
            assert "run" in result
            assert result["run"] is not None

    def test_entity_discovery_patterns(self, evaluator):
        """Test the entity discovery patterns from documentation examples"""
        # Test: What acquisitions are available?
        parser = BIQLParser.from_string("SELECT DISTINCT acq WHERE acq")
        query = parser.parse()
        results = evaluator.evaluate(query)

        # Should only return files that have acq entity
        for result in results:
            assert "acq" in result
            assert result["acq"] is not None
            assert result["acq"] != ""

        # Test: What echo times are used?
        parser = BIQLParser.from_string(
            "SELECT DISTINCT metadata.EchoTime WHERE metadata.EchoTime ORDER BY metadata.EchoTime"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)

        # Should only return files with EchoTime metadata
        for result in results:
            if "metadata.EchoTime" in result:
                echo_time = result["metadata.EchoTime"]
                assert echo_time is not None
                # Should be a numeric value
                if echo_time is not None:
                    assert isinstance(echo_time, (int, float))

        # Verify ordering if results exist
        if len(results) > 1:
            echo_times = [
                r.get("metadata.EchoTime")
                for r in results
                if r.get("metadata.EchoTime") is not None
            ]
            if len(echo_times) > 1:
                assert echo_times == sorted(echo_times)

    def test_distinct_with_vs_without_where_clause(self, evaluator):
        """Test difference between DISTINCT with and without WHERE clause for null filtering"""
        # Test with a field that likely has some null values (run)

        # Get all distinct run values (including null)
        parser = BIQLParser.from_string("SELECT DISTINCT run")
        query = parser.parse()
        all_runs = evaluator.evaluate(query)

        # Get only non-null run values
        parser = BIQLParser.from_string("SELECT DISTINCT run WHERE run")
        query = parser.parse()
        non_null_runs = evaluator.evaluate(query)

        # The WHERE clause should filter out null values
        assert len(non_null_runs) <= len(all_runs)

        # Check that all non_null_runs actually have non-null run values
        for result in non_null_runs:
            assert "run" in result
            assert result["run"] is not None

        # Check if we found the null case (some files without run)
        null_runs = [r for r in all_runs if r.get("run") is None]
        non_null_runs_from_all = [r for r in all_runs if r.get("run") is not None]

        if len(null_runs) > 0:
            # We have files without run values - verify filtering works
            assert len(non_null_runs) == len(non_null_runs_from_all)
            assert len(all_runs) == len(non_null_runs) + len(null_runs)
            print(
                f"Found {len(null_runs)} files without run values - WHERE clause properly filtered them"
            )
        else:
            # All files have run values - both queries should return same results
            assert len(all_runs) == len(non_null_runs)
            print(
                "All files have run values - WHERE clause has no effect (both queries identical)"
            )

        # Test with a metadata field that's more likely to have nulls
        parser = BIQLParser.from_string("SELECT DISTINCT metadata.EchoTime")
        query = parser.parse()
        all_echo_times = evaluator.evaluate(query)

        parser = BIQLParser.from_string(
            "SELECT DISTINCT metadata.EchoTime WHERE metadata.EchoTime"
        )
        query = parser.parse()
        non_null_echo_times = evaluator.evaluate(query)

        # Should filter out null metadata
        assert len(non_null_echo_times) <= len(all_echo_times)

        # All non-null results should have actual EchoTime values
        for result in non_null_echo_times:
            if "metadata.EchoTime" in result:
                assert result["metadata.EchoTime"] is not None

    def test_distinct_null_filtering_controlled_example(self):
        """Test DISTINCT with/without WHERE using controlled dataset to show exact difference"""
        import json
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            (tmpdir / "dataset_description.json").write_text(
                json.dumps({"Name": "Null Test Dataset", "BIDSVersion": "1.8.0"})
            )

            # Create files: some with run, some without
            test_files = [
                "sub-01/func/sub-01_task-rest_run-01_bold.nii.gz",  # Has run
                "sub-01/func/sub-01_task-rest_run-02_bold.nii.gz",  # Has run
                "sub-01/anat/sub-01_T1w.nii.gz",  # No run (typical for anat)
                "sub-02/func/sub-02_task-rest_run-01_bold.nii.gz",  # Has run
                "sub-02/anat/sub-02_T1w.nii.gz",  # No run
            ]

            for file_path in test_files:
                full_path = tmpdir / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.touch()

            dataset = BIDSDataset(tmpdir)
            evaluator = BIQLEvaluator(dataset)

            # Test 1: All distinct run values (including null)
            parser = BIQLParser.from_string("SELECT DISTINCT run")
            query = parser.parse()
            all_runs = evaluator.evaluate(query)

            # Test 2: Only non-null run values
            parser = BIQLParser.from_string("SELECT DISTINCT run WHERE run")
            query = parser.parse()
            non_null_runs = evaluator.evaluate(query)

            # Verify the expected difference
            print(f"All distinct runs: {[r.get('run') for r in all_runs]}")
            print(f"Non-null runs: {[r.get('run') for r in non_null_runs]}")

            # Should find: null, "01", "02" vs just "01", "02"
            assert len(all_runs) == 3  # [null, "01", "02"]
            assert len(non_null_runs) == 2  # ["01", "02"]

            # Verify null is in all_runs but not in non_null_runs
            null_count_all = len([r for r in all_runs if r.get("run") is None])
            null_count_filtered = len(
                [r for r in non_null_runs if r.get("run") is None]
            )

            assert null_count_all == 1  # One null entry in unfiltered results
            assert null_count_filtered == 0  # No null entries in filtered results

            # Verify the non-null entries match
            runs_all = [r.get("run") for r in all_runs if r.get("run") is not None]
            runs_filtered = [r.get("run") for r in non_null_runs]

            assert sorted(runs_all) == sorted(runs_filtered)  # Same non-null values

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

    @pytest.fixture
    def reserved_keyword_dataset(self):
        """Create a test dataset with reserved keywords in participants.tsv"""
        tmpdir = Path(tempfile.mkdtemp())

        # Dataset description
        (tmpdir / "dataset_description.json").write_text(
            json.dumps({"Name": "ReservedKeywordTest", "BIDSVersion": "1.8.0"})
        )

        # Participants file with 'group' field (reserved keyword)
        (tmpdir / "participants.tsv").write_text(
            "participant_id\tage\tsex\tgroup\tsite\n"
            "sub-01\t25\tF\tcontrol\tSiteA\n"
            "sub-02\t28\tM\tpatient\tSiteA\n"
            "sub-03\t22\tF\tcontrol\tSiteB\n"
        )

        # Create test files with specific naming for type coercion tests
        files = [
            ("sub-01/anat/sub-01_T1w.nii.gz", {}),
            ("sub-01/func/sub-01_task-rest_bold.nii.gz", {"RepetitionTime": 2.0}),
            ("sub-02/anat/sub-02_T1w.nii.gz", {}),
            ("sub-02/func/sub-02_task-rest_bold.nii.gz", {"RepetitionTime": 2.0}),
            ("sub-03/func/sub-03_task-rest_bold.nii.gz", {"RepetitionTime": 2.0}),
        ]

        for file_path, metadata in files:
            full_path = tmpdir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.touch()

            # Create JSON metadata if provided
            if metadata:
                json_path = full_path.with_suffix(".json")
                json_path.write_text(json.dumps(metadata))

        return BIDSDataset(tmpdir)

    @pytest.fixture
    def reserved_keyword_evaluator(self, reserved_keyword_dataset):
        """Evaluator for reserved keyword dataset"""
        return BIQLEvaluator(reserved_keyword_dataset)

    def test_reserved_keyword_participants_group_parsing(
        self, reserved_keyword_evaluator
    ):
        """Test that participants.group parses correctly despite 'group' being a reserved keyword"""
        # Test basic SELECT with reserved keyword
        parser = BIQLParser.from_string("SELECT participants.group")
        query = parser.parse()
        results = reserved_keyword_evaluator.evaluate(query)

        assert len(results) > 0
        for result in results:
            group_value = result.get(
                "participants.GROUP"
            )  # Note: uppercase due to keyword conversion
            assert group_value in ["control", "patient"]

    def test_reserved_keyword_participants_group_filtering(
        self, reserved_keyword_evaluator
    ):
        """Test filtering by participants.group field"""
        # Test WHERE clause with reserved keyword
        parser = BIQLParser.from_string(
            "SELECT sub, participants.group WHERE participants.group=control"
        )
        query = parser.parse()
        results = reserved_keyword_evaluator.evaluate(query)

        assert len(results) > 0
        for result in results:
            group_value = result.get("participants.GROUP")
            assert group_value == "control"
            assert result.get("sub") in ["01", "03"]  # Only subjects with control group

    def test_in_operator_numeric_string_coercion(self, reserved_keyword_evaluator):
        """Test IN operator with numbers that should match zero-padded string subjects"""
        # Test basic number to zero-padded string conversion
        parser = BIQLParser.from_string("sub IN [1, 2, 3]")
        query = parser.parse()
        results = reserved_keyword_evaluator.evaluate(query)

        assert len(results) > 0
        subjects_found = set(result.get("sub") for result in results)
        assert subjects_found.issubset({"01", "02", "03"})

    def test_in_operator_mixed_numeric_formats(self, reserved_keyword_evaluator):
        """Test IN operator with mixed numeric formats"""
        # Test both padded and unpadded numbers
        parser = BIQLParser.from_string("sub IN [01, 2, 03]")
        query = parser.parse()
        results = reserved_keyword_evaluator.evaluate(query)

        assert len(results) > 0
        subjects_found = set(result.get("sub") for result in results)
        assert subjects_found.issubset({"01", "02", "03"})

    def test_combined_fixes_reserved_keyword_and_type_coercion(
        self, reserved_keyword_evaluator
    ):
        """Test both fixes working together: reserved keyword and IN operator coercion"""
        # Test complex query using both fixes
        parser = BIQLParser.from_string(
            "SELECT participants.group WHERE sub IN [1, 3] AND participants.group=control"
        )
        query = parser.parse()
        results = reserved_keyword_evaluator.evaluate(query)

        assert len(results) > 0
        for result in results:
            group_value = result.get("participants.GROUP")
            assert group_value == "control"

        # Verify we only got subjects 01 and 03 (which are control group)
        # Get the source subjects by looking at the files
        subjects_in_results = set()
        for result in results:
            # Get subject from filename or entities
            if "sub" in result:
                subjects_in_results.add(result["sub"])

        # Both sub-01 and sub-03 should be found since they're in the IN list and are control group
        assert subjects_in_results.issubset({"01", "03"})

    def test_computed_field_wildcard_patterns(self, reserved_keyword_evaluator):
        """Test wildcard patterns with computed fields like filename, filepath"""
        # Test filename wildcard matching
        parser = BIQLParser.from_string("SELECT filename WHERE filename=*bold*")
        query = parser.parse()
        results = reserved_keyword_evaluator.evaluate(query)

        assert len(results) > 0
        for result in results:
            filename = result.get("filename")
            assert filename is not None
            assert "bold" in filename

        # Test T1w pattern
        parser = BIQLParser.from_string("SELECT filename WHERE filename=*T1w*")
        query = parser.parse()
        results = reserved_keyword_evaluator.evaluate(query)

        assert len(results) > 0
        for result in results:
            filename = result.get("filename")
            assert filename is not None
            assert "T1w" in filename

        # Test filepath pattern - should only return func files
        parser = BIQLParser.from_string("SELECT filepath WHERE filepath=*/func/*")
        query = parser.parse()
        results = reserved_keyword_evaluator.evaluate(query)

        # Should only return functional files (not anat files)
        assert len(results) > 0
        func_count = 0
        for result in results:
            filepath = result.get("filepath")
            assert filepath is not None
            if "/func/" in filepath:
                func_count += 1

        # All results should be func files
        assert func_count == len(
            results
        ), f"Expected all {len(results)} results to be func files, but only {func_count} were"

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

    def test_count_distinct_functionality(self):
        """Test COUNT(DISTINCT field) functionality"""
        # Create test data with duplicate values
        test_files = [
            {"sub": "01", "task": "rest", "run": "1", "datatype": "func"},
            {"sub": "01", "task": "rest", "run": "2", "datatype": "func"},
            {"sub": "01", "task": "nback", "run": "1", "datatype": "func"},
            {"sub": "02", "task": "rest", "run": "1", "datatype": "func"},
            {"sub": "02", "task": "rest", "run": "2", "datatype": "func"},
        ]

        class MockDataset:
            def __init__(self):
                self.files = []
                for file_data in test_files:
                    mock_file = type("MockFile", (), {})()
                    mock_file.entities = file_data
                    mock_file.metadata = {}
                    mock_file.filepath = Path(f"/test/{file_data['sub']}.nii")
                    mock_file.relative_path = Path(f"{file_data['sub']}.nii")
                    self.files.append(mock_file)
                self.participants = {}

        dataset = MockDataset()
        evaluator = BIQLEvaluator(dataset)

        # Test COUNT(DISTINCT sub) - should return 2 (sub-01, sub-02)
        parser = BIQLParser.from_string("SELECT COUNT(DISTINCT sub) as unique_subjects")
        query = parser.parse()
        results = evaluator.evaluate(query)

        assert len(results) == 1
        assert results[0]["unique_subjects"] == 2

        # Test COUNT(DISTINCT task) - should return 2 (rest, nback)
        parser = BIQLParser.from_string("SELECT COUNT(DISTINCT task) as unique_tasks")
        query = parser.parse()
        results = evaluator.evaluate(query)

        assert len(results) == 1
        assert results[0]["unique_tasks"] == 2

        # Test COUNT(DISTINCT run) grouped by task
        parser = BIQLParser.from_string(
            """
            SELECT task, COUNT(DISTINCT run) as unique_runs
            GROUP BY task
        """
        )
        query = parser.parse()
        results = evaluator.evaluate(query)

        assert len(results) == 2

        # Find results by task
        rest_result = next(r for r in results if r["task"] == "rest")
        nback_result = next(r for r in results if r["task"] == "nback")

        assert rest_result["unique_runs"] == 2  # runs 1 and 2
        assert nback_result["unique_runs"] == 1  # only run 1

        # Test COUNT(DISTINCT sub) in HAVING clause
        parser = BIQLParser.from_string(
            """
            SELECT task, COUNT(DISTINCT sub) as unique_subjects
            GROUP BY task
            HAVING COUNT(DISTINCT sub) > 1
        """
        )
        query = parser.parse()
        results = evaluator.evaluate(query)

        # Only 'rest' task has files from multiple subjects (01 and 02)
        assert len(results) == 1
        assert results[0]["task"] == "rest"
        assert results[0]["unique_subjects"] == 2


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

        # Test nested metadata access
        parser = BIQLParser.from_string("metadata.SliceTiming[0]>0")
        query = parser.parse()
        results = evaluator.evaluate(query)

        # Test multiple metadata field comparisons
        parser = BIQLParser.from_string(
            "metadata.RepetitionTime>1 AND metadata.EchoTime<1"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)

        for result in results:
            metadata = result.get("metadata", {})
            if "RepetitionTime" in metadata and "EchoTime" in metadata:
                assert float(metadata["RepetitionTime"]) > 1
                assert float(metadata["EchoTime"]) < 1

        # Test metadata inheritance from different levels
        parser = BIQLParser.from_string(
            "SELECT filename, metadata.TaskName WHERE metadata.TaskName IS NOT NULL"
        )
        query = parser.parse()
        # Even though IS NOT NULL isn't supported, the query should parse

        # Test complex metadata queries with SELECT
        parser = BIQLParser.from_string(
            "SELECT sub, datatype, metadata.RepetitionTime, metadata.EchoTime WHERE datatype=func"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)

        for result in results:
            assert "sub" in result
            assert "datatype" in result
            # Metadata fields should be present even if None
            assert "metadata.RepetitionTime" in result or "metadata.EchoTime" in result

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

        # Test combined participant and entity filtering
        parser = BIQLParser.from_string("datatype=func AND participants.sex=M")
        query = parser.parse()
        results = evaluator.evaluate(query)

        for result in results:
            assert result["datatype"] == "func"
            # Check participant data if available
            if "participants" in result and result["participants"]:
                assert result["participants"].get("sex") == "M"

        # Test all participant fields
        parser = BIQLParser.from_string(
            "SELECT sub, participants.age, participants.sex, participants.handedness, "
            "participants.site WHERE participants.handedness=R"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)

        for result in results:
            if (
                "participants.handedness" in result
                and result["participants.handedness"] is not None
            ):
                assert result["participants.handedness"] == "R"

        # Test participant queries with GROUP BY
        parser = BIQLParser.from_string(
            "SELECT participants.sex, COUNT(*) GROUP BY participants.sex"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)

        # Should have grouped by sex
        sex_values = [r.get("participants.sex") for r in results]
        assert len(sex_values) == len(set(sex_values))  # All unique

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

        # Test question mark wildcard matching
        parser = BIQLParser.from_string("sub=0?")
        query = parser.parse()
        results = evaluator.evaluate(query)

        for result in results:
            if "sub" in result:
                # Should match subjects like 01, 02, 03, etc.
                assert len(result["sub"]) == 2
                assert result["sub"][0] == "0"

    def test_derivatives_entity_types(self, synthetic_dataset_path):
        """Test support for derivatives-specific entity types"""
        dataset = BIDSDataset(synthetic_dataset_path)
        evaluator = BIQLEvaluator(dataset)

        # Test querying atlas entity
        parser = BIQLParser.from_string("atlas=AAL")
        query = parser.parse()
        results = evaluator.evaluate(query)
        # May return empty if no atlas files exist, but should not error

        # Test querying roi entity
        parser = BIQLParser.from_string("roi=hippocampus")
        query = parser.parse()
        results = evaluator.evaluate(query)
        # May return empty if no roi files exist, but should not error

        # Test querying model entity
        parser = BIQLParser.from_string("model=glm")
        query = parser.parse()
        results = evaluator.evaluate(query)
        # May return empty if no model files exist, but should not error

        # Test combined derivatives query
        parser = BIQLParser.from_string("datatype=anat AND atlas=*")
        query = parser.parse()
        results = evaluator.evaluate(query)

        # Test SELECT with derivatives entities
        parser = BIQLParser.from_string("SELECT sub, atlas, roi WHERE datatype=anat")
        query = parser.parse()
        results = evaluator.evaluate(query)

        # All results should have the requested fields (even if None)
        for result in results:
            assert "sub" in result
            assert "atlas" in result
            assert "roi" in result


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
