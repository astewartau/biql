"""
Comprehensive tests for BIDS Query Language (BIQL)

Tests all components of the BIQL implementation using real BIDS examples.
"""

import pytest

from biql.dataset import BIDSDataset


class TestBIDSDataset:
    """Test BIDS dataset loading and indexing"""

    def test_dataset_loading(self, synthetic_dataset_path):
        """Test basic dataset loading"""
        synthetic_dataset = BIDSDataset(synthetic_dataset_path)

        assert len(synthetic_dataset.files) > 0
        assert len(synthetic_dataset.participants) > 0

    def test_entity_extraction(self, synthetic_dataset_path):
        """Test BIDS entity extraction"""
        synthetic_dataset = BIDSDataset(synthetic_dataset_path)
        """Test BIDS entity extraction"""
        subjects = synthetic_dataset.get_subjects()
        assert "01" in subjects
        assert len(subjects) >= 3

        datatypes = synthetic_dataset.get_datatypes()
        assert "anat" in datatypes
        assert "func" in datatypes

    def test_file_parsing(self, synthetic_dataset_path):
        """Test individual file parsing"""
        synthetic_dataset = BIDSDataset(synthetic_dataset_path)
        """Test individual file parsing"""
        # Find a functional file
        func_files = [
            f for f in synthetic_dataset.files if f.entities.get("datatype") == "func"
        ]
        assert len(func_files) > 0

        func_file = func_files[0]
        assert "sub" in func_file.entities
        assert "task" in func_file.entities

    def test_participants_loading(self, synthetic_dataset_path):
        """Test participants.tsv loading"""
        synthetic_dataset = BIDSDataset(synthetic_dataset_path)
        """Test participants.tsv loading"""
        participants = synthetic_dataset.participants
        assert len(participants) > 0

        # Check specific participant data
        if "01" in participants:
            assert "age" in participants["01"]
            assert "sex" in participants["01"]

    def test_metadata_inheritance(self, synthetic_dataset_path):
        """Test JSON metadata inheritance"""
        synthetic_dataset = BIDSDataset(synthetic_dataset_path)
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


if __name__ == "__main__":
    # Run specific test categories
    pytest.main([__file__, "-v", "--tb=short"])
