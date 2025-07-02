"""
Shared test configuration and fixtures for BIQL tests.

This module provides utilities for downloading and setting up test data,
replacing hardcoded paths to ensure tests work in any environment.
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


class BIDSExamplesManager:
    """Manages BIDS examples repository for testing."""

    _instance = None
    _examples_dir = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_examples_dir(self):
        """Get or create a local copy of bids-examples repository."""
        if self._examples_dir is not None and self._examples_dir.exists():
            return self._examples_dir

        # Create a temporary directory that persists for the test session
        temp_dir = Path(tempfile.mkdtemp(prefix="biql_test_bids_examples_"))
        examples_dir = temp_dir / "bids-examples"

        try:
            # Clone the bids-examples repository
            subprocess.run(
                [
                    "git",
                    "clone",
                    "https://github.com/bids-standard/bids-examples.git",
                    str(examples_dir),
                ],
                check=True,
                capture_output=True,
            )

            self._examples_dir = examples_dir
            return examples_dir

        except subprocess.CalledProcessError as e:
            # If git clone fails, try to download specific datasets we need
            examples_dir.mkdir(exist_ok=True)
            self._create_minimal_synthetic_dataset(examples_dir)
            self._examples_dir = examples_dir
            return examples_dir

    def _create_minimal_synthetic_dataset(self, examples_dir):
        """Create a minimal synthetic dataset for testing when git clone fails."""
        synthetic_dir = examples_dir / "synthetic"
        synthetic_dir.mkdir(parents=True, exist_ok=True)

        # Create dataset_description.json
        import json

        dataset_desc = {
            "Name": "Synthetic BIDS Dataset",
            "BIDSVersion": "1.8.0",
            "Authors": ["Test"],
            "DatasetType": "raw",
        }
        (synthetic_dir / "dataset_description.json").write_text(
            json.dumps(dataset_desc, indent=2)
        )

        # Create participants.tsv
        participants_data = [
            "participant_id\tage\tsex\thandedness\tsite",
            "sub-01\t25\tF\tR\tSiteA",
            "sub-02\t28\tM\tR\tSiteA",
            "sub-03\t22\tF\tL\tSiteB",
            "sub-04\t30\tM\tR\tSiteB",
            "sub-05\t27\tF\tR\tSiteA",
        ]
        (synthetic_dir / "participants.tsv").write_text("\n".join(participants_data))

        # Create test files for each subject and session
        for sub in ["01", "02", "03", "04", "05"]:
            for ses in ["01", "02"]:
                # Anatomical data
                anat_dir = synthetic_dir / f"sub-{sub}" / f"ses-{ses}" / "anat"
                anat_dir.mkdir(parents=True, exist_ok=True)
                (anat_dir / f"sub-{sub}_ses-{ses}_T1w.nii.gz").touch()
                (anat_dir / f"sub-{sub}_ses-{ses}_T1w.json").write_text(
                    '{"RepetitionTime": 2.0}'
                )

                # Functional data - nback task with 2 runs
                func_dir = synthetic_dir / f"sub-{sub}" / f"ses-{ses}" / "func"
                func_dir.mkdir(parents=True, exist_ok=True)

                for run in ["01", "02"]:
                    # BOLD files
                    bold_file = (
                        func_dir
                        / f"sub-{sub}_ses-{ses}_task-nback_run-{run}_bold.nii.gz"
                    )
                    bold_file.touch()

                    # JSON metadata
                    bold_json = (
                        func_dir / f"sub-{sub}_ses-{ses}_task-nback_run-{run}_bold.json"
                    )
                    bold_json.write_text(
                        json.dumps(
                            {
                                "RepetitionTime": 2.0,
                                "EchoTime": 0.03,
                                "TaskName": "nback",
                            }
                        )
                    )

    def cleanup(self):
        """Cleanup the examples directory."""
        if self._examples_dir and self._examples_dir.exists():
            self._safe_rmtree(self._examples_dir.parent)
            self._examples_dir = None

    def _safe_rmtree(self, path):
        """Safely remove directory tree, handling Windows permission issues."""
        import stat
        import sys

        def handle_remove_readonly(func, path, exc_info):
            """Error handler for removing read-only files on Windows."""
            if os.path.exists(path):
                # Make the file writable and try again
                os.chmod(path, stat.S_IWRITE)
                func(path)

        try:
            # Use onexc for Python 3.12+ or onerror for older versions
            if sys.version_info >= (3, 12):
                shutil.rmtree(path, onexc=handle_remove_readonly)
            else:
                shutil.rmtree(path, onerror=handle_remove_readonly)
        except (OSError, PermissionError):
            # If cleanup still fails, try a more aggressive approach
            try:
                if os.name == "nt":  # Windows
                    # On Windows, use subprocess to force remove
                    subprocess.run(
                        ["rmdir", "/S", "/Q", str(path)],
                        shell=True,
                        capture_output=True,
                    )
                else:
                    # On Unix-like systems, use rm -rf as fallback
                    subprocess.run(["rm", "-rf", str(path)], capture_output=True)
            except Exception:
                # If all cleanup attempts fail, just ignore the error
                # The temp directory will be cleaned up by the OS eventually
                pass


# Global instance
_bids_examples_manager = BIDSExamplesManager()


@pytest.fixture(scope="session")
def bids_examples_dir():
    """Session-scoped fixture providing path to bids-examples directory."""
    examples_dir = _bids_examples_manager.get_examples_dir()
    yield examples_dir
    # Cleanup happens at session end
    _bids_examples_manager.cleanup()


@pytest.fixture
def synthetic_dataset_path(bids_examples_dir):
    """Fixture providing path to synthetic BIDS dataset."""
    synthetic_path = bids_examples_dir / "synthetic"
    if not synthetic_path.exists():
        pytest.fail("Synthetic dataset not available")
    return str(synthetic_path)
