"""
Comprehensive tests for BIDS Query Language (BIQL)

Tests all components of the BIQL implementation using real BIDS examples.
"""

import pytest


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


if __name__ == "__main__":
    # Run specific test categories
    pytest.main([__file__, "-v", "--tb=short"])
