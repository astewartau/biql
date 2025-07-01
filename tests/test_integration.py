"""
Comprehensive tests for BIDS Query Language (BIQL)

Tests all components of the BIQL implementation using real BIDS examples.
"""

import pytest

from biql.dataset import BIDSDataset
from biql.evaluator import BIQLEvaluator
from biql.formatter import BIQLFormatter
from biql.parser import BIQLParser


class TestIntegration:
    """Integration tests using real BIDS datasets"""

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


if __name__ == "__main__":
    # Run specific test categories
    pytest.main([__file__, "-v", "--tb=short"])
