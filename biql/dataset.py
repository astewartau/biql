"""
BIDS Dataset representation and indexing

Handles loading and indexing BIDS datasets for querying.
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Set


@dataclass
class BIDSFile:
    """Represents a BIDS file with entities and metadata"""

    def __init__(self, filepath: Path, dataset_root: Path):
        self.filepath = filepath
        self.dataset_root = dataset_root
        self.relative_path = filepath.relative_to(dataset_root)
        self.entities = self._parse_entities()
        self.metadata = self._load_metadata()

    def _parse_entities(self) -> Dict[str, str]:
        """Parse BIDS entities from filename and path"""
        entities = {}
        filename = self.filepath.name

        # Remove extension(s)
        name_parts = filename.split(".")
        name_without_ext = name_parts[0]

        # Parse entities from filename
        parts = name_without_ext.split("_")
        for part in parts:
            if "-" in part:
                key, value = part.split("-", 1)
                entities[key] = value
            else:
                # This is the suffix
                entities["suffix"] = part

        # Add datatype from parent directory
        parent = self.filepath.parent.name
        if parent in [
            "anat",
            "func",
            "dwi",
            "fmap",
            "perf",
            "meg",
            "eeg",
            "ieeg",
            "beh",
            "pet",
            "micr",
            "nirs",
            "motion",
            "mrs",
        ]:
            entities["datatype"] = parent

        # Add extension
        if len(name_parts) > 1:
            entities["extension"] = "." + ".".join(name_parts[1:])

        # Extract subject and session from path if not in filename
        path_parts = str(self.relative_path).split(os.sep)
        for part in path_parts:
            if part.startswith("sub-") and "sub" not in entities:
                entities["sub"] = part[4:]  # Remove 'sub-' prefix
            elif part.startswith("ses-") and "ses" not in entities:
                entities["ses"] = part[4:]  # Remove 'ses-' prefix

        return entities

    def _load_metadata(self) -> Dict[str, Any]:
        """Load JSON sidecar metadata with inheritance"""
        metadata = {}

        # Start from the most specific and work up the hierarchy
        current_path = self.filepath

        # Check for direct JSON sidecar
        json_path = current_path.parent / (current_path.stem + ".json")
        if json_path.exists():
            with open(json_path, "r") as f:
                metadata.update(json.load(f))

        # Apply inheritance principle - check parent directories
        current_dir = self.filepath.parent
        file_entities = self.entities.copy()

        while current_dir != self.dataset_root and current_dir != current_dir.parent:
            # Look for applicable JSON files in current directory
            for json_file in current_dir.glob("*.json"):
                if self._is_applicable_metadata(json_file, file_entities):
                    with open(json_file, "r") as f:
                        parent_metadata = json.load(f)
                        # Parent metadata doesn't override existing
                        for key, value in parent_metadata.items():
                            if key not in metadata:
                                metadata[key] = value

            current_dir = current_dir.parent

        return metadata

    def _is_applicable_metadata(
        self, json_path: Path, file_entities: Dict[str, str]
    ) -> bool:
        """Check if metadata file applies to this file per BIDS inheritance"""
        json_name = json_path.stem

        # Skip if it's the same file
        if json_name == self.filepath.stem:
            return False

        # Parse entities from JSON filename
        json_entities = {}
        parts = json_name.split("_")
        for part in parts:
            if "-" in part:
                key, value = part.split("-", 1)
                json_entities[key] = value

        # Check if all entities in JSON name are compatible with file
        for key, value in json_entities.items():
            if key in file_entities and file_entities[key] != value:
                return False

        return True


class BIDSDataset:
    """Represents a BIDS dataset with indexed files"""

    def __init__(self, root_path: Path):
        self.root = Path(root_path).resolve()
        if not self.root.exists():
            raise ValueError(f"Dataset path does not exist: {self.root}")

        self.files = self._index_files()
        self.participants = self._load_participants()
        self.dataset_description = self._load_dataset_description()

    def _index_files(self) -> List[BIDSFile]:
        """Index all BIDS files in the dataset"""
        files = []

        # Common BIDS file patterns
        patterns = [
            "**/*.nii.gz",
            "**/*.nii",
            "**/*.tsv",
            "**/*.json",
            "**/*.edf",
            "**/*.vhdr",
            "**/*.set",
            "**/*.fif",
            "**/*.mat",
            "**/*.txt",
            "**/*.bvec",
            "**/*.bval",
        ]

        indexed_files = set()

        for pattern in patterns:
            for filepath in self.root.glob(pattern):
                # Skip if already indexed
                if filepath in indexed_files:
                    continue

                # Skip hidden files and directories
                if any(part.startswith(".") for part in filepath.parts):
                    continue

                # Skip top-level BIDS files
                if filepath.parent == self.root and filepath.name in [
                    "participants.tsv",
                    "participants.json",
                    "dataset_description.json",
                    "README",
                    "CHANGES",
                    "code",
                    "derivatives",
                    "sourcedata",
                ]:
                    continue

                # Skip if it's in excluded directories
                if any(
                    part in ["code", "derivatives", "sourcedata"]
                    for part in filepath.parts
                ):
                    continue

                try:
                    bids_file = BIDSFile(filepath, self.root)
                    # Only include files that look like BIDS files
                    if self._is_bids_file(bids_file):
                        files.append(bids_file)
                        indexed_files.add(filepath)
                except Exception:
                    # Skip files that don't parse as BIDS
                    pass

        return files

    def _is_bids_file(self, bids_file: BIDSFile) -> bool:
        """Check if file appears to be a valid BIDS file"""
        # Must have at least a subject or be in a datatype directory
        has_subject = "sub" in bids_file.entities
        has_datatype = "datatype" in bids_file.entities

        # Check if path structure looks like BIDS
        path_parts = str(bids_file.relative_path).split(os.sep)
        has_sub_dir = any(part.startswith("sub-") for part in path_parts)

        return (has_subject or has_sub_dir) and (has_datatype or len(path_parts) > 1)

    def _load_participants(self) -> Dict[str, Dict[str, Any]]:
        """Load participants.tsv if available"""
        participants = {}
        participants_file = self.root / "participants.tsv"

        if participants_file.exists():
            try:
                with open(participants_file, "r") as f:
                    lines = f.readlines()
                    if len(lines) > 1:
                        headers = lines[0].strip().split("\t")
                        for line in lines[1:]:
                            values = line.strip().split("\t")
                            if values and values[0].startswith("sub-"):
                                participant_id = values[0].replace("sub-", "")
                                participant_data = {}
                                for i, header in enumerate(headers[1:], 1):
                                    if i < len(values):
                                        # Try to convert to appropriate type
                                        value = values[i]
                                        if value == "n/a" or value == "":
                                            value = None
                                        elif value.replace(".", "").isdigit():
                                            value = (
                                                float(value)
                                                if "." in value
                                                else int(value)
                                            )
                                        participant_data[header] = value
                                participants[participant_id] = participant_data
            except Exception:
                # Skip if participants.tsv is malformed
                pass

        return participants

    def _load_dataset_description(self) -> Dict[str, Any]:
        """Load dataset_description.json if available"""
        desc_file = self.root / "dataset_description.json"
        if desc_file.exists():
            try:
                with open(desc_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def get_subjects(self) -> Set[str]:
        """Get all unique subjects in dataset"""
        subjects = set()
        for file in self.files:
            if "sub" in file.entities:
                subjects.add(file.entities["sub"])
        return subjects

    def get_sessions(self) -> Set[str]:
        """Get all unique sessions in dataset"""
        sessions = set()
        for file in self.files:
            if "ses" in file.entities:
                sessions.add(file.entities["ses"])
        return sessions

    def get_datatypes(self) -> Set[str]:
        """Get all unique datatypes in dataset"""
        datatypes = set()
        for file in self.files:
            if "datatype" in file.entities:
                datatypes.add(file.entities["datatype"])
        return datatypes

    def get_tasks(self) -> Set[str]:
        """Get all unique tasks in dataset"""
        tasks = set()
        for file in self.files:
            if "task" in file.entities:
                tasks.add(file.entities["task"])
        return tasks

    def get_entities(self) -> Set[str]:
        """Get all unique entity keys in dataset"""
        entities = set()
        for file in self.files:
            entities.update(file.entities.keys())
        return entities
