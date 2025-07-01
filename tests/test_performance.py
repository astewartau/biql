"""
Performance tests for BIDS Query Language (BIQL)

Tests performance characteristics and scalability.
"""

import time

import pytest

from biql.dataset import BIDSDataset
from biql.evaluator import BIQLEvaluator
from biql.parser import BIQLParser


class TestPerformance:
    """Test BIQL performance characteristics"""

    @pytest.fixture
    def large_dataset(self, bids_examples_dir):
        """Fixture for largest available BIDS dataset"""
        # Try to find the largest dataset for performance testing
        candidates = [
            "ds000117",  # MEG dataset with many files
            "ds107",  # Large dataset with many subjects
            "synthetic",  # Fallback
        ]

        for candidate in candidates:
            path = bids_examples_dir / candidate
            if path.exists():
                return BIDSDataset(path)

        # Fallback to synthetic if available
        synthetic_path = bids_examples_dir / "synthetic"
        if synthetic_path.exists():
            return BIDSDataset(synthetic_path)

        # If no datasets found, return synthetic dataset from conftest
        return BIDSDataset(bids_examples_dir / "synthetic")

    def test_dataset_loading_performance(self, large_dataset):
        """Test dataset loading performance"""
        start_time = time.time()

        # Re-create dataset to test loading time
        dataset = BIDSDataset(large_dataset.root)

        load_time = time.time() - start_time

        # Should load reasonably quickly (adjust threshold as needed)
        assert load_time < 30.0  # 30 seconds max
        assert len(dataset.files) > 0

    def test_simple_query_performance(self, large_dataset):
        """Test simple query performance"""
        evaluator = BIQLEvaluator(large_dataset)

        start_time = time.time()

        parser = BIQLParser.from_string("datatype=func")
        query = parser.parse()
        evaluator.evaluate(query)

        query_time = time.time() - start_time

        # Simple queries should be fast
        assert query_time < 5.0  # 5 seconds max

    def test_complex_query_performance(self, large_dataset):
        """Test complex query performance"""
        evaluator = BIQLEvaluator(large_dataset)

        start_time = time.time()

        parser = BIQLParser.from_string(
            "SELECT sub, ses, task, run, filepath WHERE "
            "(datatype=func OR datatype=anat) AND "
            '(task=rest OR task~=".*back.*") '
            "ORDER BY sub, ses, run"
        )
        query = parser.parse()
        evaluator.evaluate(query)

        query_time = time.time() - start_time

        # Complex queries should still complete in reasonable time
        assert query_time < 10.0  # 10 seconds max

    def test_metadata_query_performance(self, large_dataset):
        """Test metadata query performance"""
        evaluator = BIQLEvaluator(large_dataset)

        start_time = time.time()

        parser = BIQLParser.from_string("metadata.RepetitionTime>0")
        query = parser.parse()
        evaluator.evaluate(query)

        query_time = time.time() - start_time

        # Metadata queries might be slower due to JSON parsing
        assert query_time < 15.0  # 15 seconds max

    def test_aggregation_performance(self, large_dataset):
        """Test aggregation query performance"""
        evaluator = BIQLEvaluator(large_dataset)

        start_time = time.time()

        parser = BIQLParser.from_string("SELECT sub, COUNT(*) GROUP BY sub")
        query = parser.parse()
        evaluator.evaluate(query)

        query_time = time.time() - start_time

        # Aggregation should be reasonably fast
        assert query_time < 8.0  # 8 seconds max

    def test_pattern_matching_performance(self, large_dataset):
        """Test pattern matching performance"""
        evaluator = BIQLEvaluator(large_dataset)

        start_time = time.time()

        parser = BIQLParser.from_string('suffix~=".*bold.*" AND sub~="0[1-5]"')
        query = parser.parse()
        evaluator.evaluate(query)

        query_time = time.time() - start_time

        # Pattern matching might be slower
        assert query_time < 12.0  # 12 seconds max

    def test_memory_usage(self, large_dataset):
        """Test memory usage characteristics"""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        evaluator = BIQLEvaluator(large_dataset)

        # Run several queries to see memory growth
        queries = [
            "datatype=func",
            "datatype=anat",
            "task=rest",
            "SELECT sub, task, filepath WHERE datatype=func",
            "SELECT sub, COUNT(*) GROUP BY sub",
        ]

        for query_str in queries:
            parser = BIQLParser.from_string(query_str)
            query = parser.parse()
            evaluator.evaluate(query)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - initial_memory

        # Memory growth should be reasonable
        assert memory_growth < 500  # Less than 500MB growth

    def test_scalability_with_file_count(self):
        """Test how performance scales with file count"""
        # Test with different sized datasets if available
        datasets_by_size = []

        # Use fixture since we no longer have hardcoded path
        pytest.skip(
            "Scalability testing requires multiple datasets - not implemented for conftest setup"
        )

        if len(datasets_by_size) < 2:
            pytest.skip("Need multiple datasets for scalability testing")

        datasets_by_size.sort(key=lambda x: x[0])

        query_times = []

        for file_count, dataset in datasets_by_size:
            evaluator = BIQLEvaluator(dataset)

            start_time = time.time()

            parser = BIQLParser.from_string("datatype=func OR datatype=anat")
            query = parser.parse()
            evaluator.evaluate(query)

            query_time = time.time() - start_time
            query_times.append((file_count, query_time))

        # Check that query time doesn't grow too quickly with file count
        if len(query_times) >= 2:
            small_files, small_time = query_times[0]
            large_files, large_time = query_times[-1]

            if (
                large_files > small_files * 2
            ):  # Only test if significant size difference
                # Time should not grow more than quadratically with file count
                time_ratio = large_time / small_time if small_time > 0 else 1
                file_ratio = large_files / small_files if small_files > 0 else 1

                # Very loose constraint - just ensure it's not exponential
                assert time_ratio < file_ratio**2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
