"""
Comprehensive tests for BIDS Query Language (BIQL)

Tests all components of the BIQL implementation using real BIDS examples.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from biql.dataset import BIDSDataset
from biql.evaluator import BIQLEvaluator
from biql.parser import BIQLParser


class TestBIQLEvaluator:
    """Test BIQL query evaluation"""

    @pytest.fixture
    def synthetic_dataset(self, synthetic_dataset_path):
        """Fixture for synthetic BIDS dataset"""
        return BIDSDataset(synthetic_dataset_path)

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

    def test_range_syntax_returns_empty_list(self, evaluator):
        """Test the exact issue reported: run=[1:2] returns [] while run IN [1,2] returns results"""
        # User's exact query that returns empty list
        parser_range = BIQLParser.from_string("SELECT sub WHERE run=[1:2]")
        query_range = parser_range.parse()
        results_range = evaluator.evaluate(query_range)

        # User's working query with IN syntax
        parser_in = BIQLParser.from_string("SELECT sub WHERE run IN [1,2]")
        query_in = parser_in.parse()
        results_in = evaluator.evaluate(query_in)

        # IN syntax should return 20 results (5 subjects × 2 sessions × 2 runs)
        assert (
            len(results_in) == 20
        ), f"Expected 20 results from IN syntax, got {len(results_in)}"

        # Range syntax should return the same results but currently returns []
        assert (
            len(results_range) == 20
        ), f"Range syntax [1:2] should return 20 results but returned {len(results_range)}"

        # Verify the results are identical
        subs_range = sorted([r["sub"] for r in results_range])
        subs_in = sorted([r["sub"] for r in results_in])
        assert (
            subs_range == subs_in
        ), f"Range returned {subs_range}, IN returned {subs_in}"

    def test_range_vs_in_syntax(self, evaluator):
        """Test that range syntax [1:2] works the same as IN [1,2]"""
        # The synthetic dataset has 20 nback files with run-01 and run-02
        # (5 subjects × 2 sessions × 2 runs = 20 files)

        # Test with range syntax
        parser_range = BIQLParser.from_string(
            "SELECT sub, task, run WHERE run=[1:2] AND datatype=func"
        )
        query_range = parser_range.parse()
        results_range = evaluator.evaluate(query_range)

        # Test with IN syntax
        parser_in = BIQLParser.from_string(
            "SELECT sub, task, run WHERE run IN [1,2] AND datatype=func"
        )
        query_in = parser_in.parse()
        results_in = evaluator.evaluate(query_in)

        # We expect 20 results (all nback files with run-01 or run-02)
        assert (
            len(results_in) == 20
        ), f"IN syntax should return 20 results, got {len(results_in)}"
        assert (
            len(results_range) == 20
        ), f"Range syntax should return 20 results, got {len(results_range)}"

        # Extract run values from both result sets
        runs_range = sorted([r["run"] for r in results_range if "run" in r])
        runs_in = sorted([r["run"] for r in results_in if "run" in r])

        # Both should have the same run values
        assert (
            runs_range == runs_in
        ), f"Range syntax matched runs {runs_range}, IN syntax matched runs {runs_in}"

        # All results should have run values of 01 or 02
        for result in results_range:
            assert result["run"] in [
                "01",
                "02",
            ], f"Unexpected run value: {result['run']}"
            assert (
                result["task"] == "nback"
            ), f"Expected task=nback, got {result['task']}"

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

    def test_parenthesized_distinct_syntax(self, evaluator):
        """Test new (DISTINCT field) syntax"""
        parser = BIQLParser.from_string(
            "SELECT sub, (DISTINCT task) as tasks, COUNT(*) as total_files GROUP BY sub"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)

        for result in results:
            assert "tasks" in result
            assert "total_files" in result
            assert isinstance(result["tasks"], list)
            assert isinstance(result["total_files"], int)

            # Each subject should have unique tasks only
            tasks = result["tasks"]
            assert len(tasks) == len(set(tasks)), "DISTINCT should remove duplicates"

            # Should have the basic tasks
            for task in tasks:
                assert task in [None, "rest", "nback", "stroop"]

    def test_parenthesized_non_distinct_syntax(self, evaluator):
        """Test new (field) syntax without DISTINCT - should include duplicates"""
        parser = BIQLParser.from_string(
            "SELECT sub, (task) as all_tasks, COUNT(*) as total_files WHERE sub='01' GROUP BY sub"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)

        assert len(results) == 1
        result = results[0]

        assert "all_tasks" in result
        assert "total_files" in result
        assert isinstance(result["all_tasks"], list)
        assert isinstance(result["total_files"], int)

        # Without DISTINCT, should include duplicates
        all_tasks = result["all_tasks"]
        total_files = result["total_files"]

        # The number of tasks should equal the total files (each file has a task)
        assert (
            len(all_tasks) == total_files
        ), f"Expected {total_files} tasks, got {len(all_tasks)}"

        # Should contain duplicates
        unique_tasks = list(set(all_tasks))
        assert len(unique_tasks) < len(
            all_tasks
        ), "Non-DISTINCT should contain duplicates"

    def test_parenthesized_where_condition_syntax(self, evaluator):
        """Test new (field WHERE condition) syntax"""
        parser = BIQLParser.from_string(
            "SELECT sub, (filename WHERE suffix='bold') as bold_files GROUP BY sub"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)

        for result in results:
            assert "bold_files" in result
            assert isinstance(result["bold_files"], list)

            # All filenames should contain 'bold'
            for filename in result["bold_files"]:
                assert "bold" in filename

    def test_parenthesized_distinct_where_syntax(self, evaluator):
        """Test new (DISTINCT field WHERE condition) syntax"""
        parser = BIQLParser.from_string(
            "SELECT sub, (DISTINCT datatype WHERE datatype IS NOT NULL) as datatypes GROUP BY sub"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)

        for result in results:
            assert "datatypes" in result
            assert isinstance(result["datatypes"], list)

            # Should only contain unique datatypes
            datatypes = result["datatypes"]
            assert len(datatypes) == len(
                set(datatypes)
            ), "DISTINCT should remove duplicates"

            # Should not contain None values due to WHERE condition
            assert None not in datatypes

    def test_parenthesized_vs_array_agg_equivalence(self, evaluator):
        """Test that new syntax is equivalent to ARRAY_AGG"""
        # Test DISTINCT equivalence
        parser1 = BIQLParser.from_string(
            "SELECT sub, (DISTINCT task) as tasks GROUP BY sub"
        )
        query1 = parser1.parse()
        results1 = evaluator.evaluate(query1)

        parser2 = BIQLParser.from_string(
            "SELECT sub, ARRAY_AGG(DISTINCT task) as tasks GROUP BY sub"
        )
        query2 = parser2.parse()
        results2 = evaluator.evaluate(query2)

        # Sort results by sub for comparison
        results1.sort(key=lambda x: x["sub"])
        results2.sort(key=lambda x: x["sub"])

        assert len(results1) == len(results2)
        for r1, r2 in zip(results1, results2):
            assert r1["sub"] == r2["sub"]
            assert sorted(r1["tasks"]) == sorted(r2["tasks"])

    def test_parenthesized_duplicates_count_consistency(self, evaluator):
        """Test that non-DISTINCT arrays have consistent counts"""
        parser = BIQLParser.from_string(
            "SELECT sub, (task) as all_tasks, (datatype) as all_datatypes, COUNT(*) as total "
            "WHERE sub IN ['01', '02'] GROUP BY sub"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)

        for result in results:
            all_tasks = result["all_tasks"]
            all_datatypes = result["all_datatypes"]
            total = result["total"]

            # All arrays should have the same length as COUNT(*)
            assert (
                len(all_tasks) == total
            ), f"Task array length {len(all_tasks)} != total {total}"
            assert (
                len(all_datatypes) == total
            ), f"Datatype array length {len(all_datatypes)} != total {total}"

    def test_array_agg_duplicates_count_consistency(self, evaluator):
        """Test that ARRAY_AGG without DISTINCT includes all values and matches COUNT(*)"""
        parser = BIQLParser.from_string(
            "SELECT sub, ARRAY_AGG(task) as tasks, COUNT(*) as total_files "
            "WHERE sub IN ['01', '02', '03'] "
            "GROUP BY sub"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)

        for result in results:
            # The number of items in the non-DISTINCT array should match COUNT(*)
            assert (
                len(result["tasks"]) == result["total_files"]
            ), f"Subject {result['sub']}: {len(result['tasks'])} tasks != {result['total_files']} files"

            # Check that None values are included
            none_count = result["tasks"].count(None)
            assert (
                none_count > 0
            ), f"Subject {result['sub']}: No None values found in tasks array"

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
                    # Items can be strings or None
                    assert all(
                        isinstance(dt, (str, type(None))) for dt in result["datatype"]
                    )
                    break

    def test_group_by_non_distinct_auto_aggregation(self, evaluator):
        """Test that non-grouped fields include all values including duplicates and None"""
        parser = BIQLParser.from_string(
            "SELECT sub, task, COUNT(*) as total " "WHERE sub='01' GROUP BY sub"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)

        assert len(results) == 1
        result = results[0]

        # Task should be an array with all values (including duplicates and None)
        assert isinstance(result["task"], list)
        assert len(result["task"]) == result["total"]

        # Should include None values
        none_count = result["task"].count(None)
        assert none_count > 0

        # Should include duplicates
        task_counts = {}
        for task in result["task"]:
            if task is not None:
                task_counts[task] = task_counts.get(task, 0) + 1

        # At least one task should appear more than once
        assert any(count > 1 for count in task_counts.values())

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
            # Use os.sep to be platform-agnostic
            func_pattern = f"{os.sep}func{os.sep}"
            if func_pattern in filepath:
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

    def test_range_syntax_formats(self, evaluator):
        """Test various range syntax formats"""
        # Test basic range [1:3] - should include 1, 2, and 3
        parser = BIQLParser.from_string("run=[1:3]")
        query = parser.parse()
        results = evaluator.evaluate(query)

        # Must return some results
        assert len(results) > 0, "Range query [1:3] returned no results"

        # Verify all runs are in range
        for result in results:
            run = result.get("run")
            if run is not None:
                try:
                    run_num = int(run)
                    assert 1 <= run_num <= 3, f"Run {run_num} outside range [1:3]"
                except ValueError:
                    pytest.fail(
                        f"Run value '{run}' cannot be converted to integer for range comparison"
                    )

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


if __name__ == "__main__":
    # Run specific test categories
    pytest.main([__file__, "-v", "--tb=short"])
