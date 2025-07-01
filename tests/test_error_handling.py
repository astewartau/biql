"""
Comprehensive tests for BIDS Query Language (BIQL)

Tests all components of the BIQL implementation using real BIDS examples.
"""

import tempfile
from pathlib import Path

import pytest

from biql.dataset import BIDSDataset
from biql.evaluator import BIQLEvaluator
from biql.parser import BIQLParser


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
