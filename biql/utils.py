"""
Utility functions for BIQL
"""

import json
import tempfile
from pathlib import Path


def create_example_dataset():
    """Create a temporary example BIDS dataset for testing and tutorials.

    Returns:
        str: Path to the created dataset
    """
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="biql_example_")
    dataset_path = Path(temp_dir)

    # Create dataset_description.json
    dataset_desc = {
        "Name": "Example BIQL Dataset",
        "BIDSVersion": "1.8.0",
        "License": "CC0",
        "Authors": ["BIQL Team"],
        "Acknowledgements": "Generated for BIQL demonstration purposes",
        "HowToAcknowledge": "Please cite BIQL",
        "DatasetType": "raw",
    }

    with open(dataset_path / "dataset_description.json", "w") as f:
        json.dump(dataset_desc, f, indent=2)

    # Create participants.tsv
    participants_data = [
        "participant_id\tage\tsex\tgroup\tsite",
        "sub-01\t25\tF\tcontrol\tSiteA",
        "sub-02\t28\tM\tpatient\tSiteA",
        "sub-03\t22\tF\tcontrol\tSiteB",
    ]

    with open(dataset_path / "participants.tsv", "w") as f:
        f.write("\n".join(participants_data))

    # Define subjects and their sessions
    subjects = {"01": ["baseline", "followup"], "02": ["baseline"], "03": ["baseline"]}

    # Create subject directories and files
    for sub_id, sessions in subjects.items():
        sub_dir = dataset_path / f"sub-{sub_id}"

        for ses_id in sessions:
            ses_dir = sub_dir / f"ses-{ses_id}"

            # Create anatomical data (only for baseline sessions)
            if ses_id == "baseline":
                anat_dir = ses_dir / "anat"
                anat_dir.mkdir(parents=True, exist_ok=True)

                # T1w files
                t1w_nii = anat_dir / f"sub-{sub_id}_ses-{ses_id}_T1w.nii.gz"
                t1w_json = anat_dir / f"sub-{sub_id}_ses-{ses_id}_T1w.json"

                # Create dummy NIfTI file
                t1w_nii.touch()

                # Create T1w JSON metadata
                t1w_metadata = {
                    "Modality": "MR",
                    "MagneticFieldStrength": 3.0,
                    "ImagingFrequency": 123.259,
                    "Manufacturer": "Siemens",
                    "ManufacturersModelName": "Prisma",
                    "InstitutionName": "Example Hospital",
                    "InstitutionalDepartmentName": "Radiology",
                    "InversionTime": 1.0,
                    "FlipAngle": 9,
                    "EchoTime": 0.00372,
                    "RepetitionTime": 2.3,
                    "VoxelSize": [1.0, 1.0, 1.0],
                    "ConversionSoftware": "dcm2niix",
                    "ConversionSoftwareVersion": "v1.0.20220720",
                }

                with open(t1w_json, "w") as f:
                    json.dump(t1w_metadata, f, indent=2)

            # Create functional data
            func_dir = ses_dir / "func"
            func_dir.mkdir(parents=True, exist_ok=True)

            # Define tasks per subject/session
            if sub_id == "01":
                if ses_id == "baseline":
                    tasks = [("nback", "01"), ("rest", None)]
                else:  # followup
                    tasks = [("nback", "01")]
            elif sub_id == "02":
                tasks = [("nback", "01"), ("nback", "02"), ("rest", None)]
            else:  # sub-03
                tasks = [("rest", None)]

            for task, run in tasks:
                # Build filename
                filename_parts = [f"sub-{sub_id}", f"ses-{ses_id}", f"task-{task}"]
                if run:
                    filename_parts.append(f"run-{run}")
                filename_parts.append("bold")

                base_filename = "_".join(filename_parts)

                # Create NIfTI and JSON files
                nii_file = func_dir / f"{base_filename}.nii.gz"
                json_file = func_dir / f"{base_filename}.json"

                # Create dummy NIfTI file
                nii_file.touch()

                # Create functional JSON metadata
                func_metadata = {
                    "TaskName": task,
                    "Modality": "MR",
                    "MagneticFieldStrength": 3.0,
                    "ImagingFrequency": 123.259,
                    "Manufacturer": "Siemens",
                    "ManufacturersModelName": "Prisma",
                    "InstitutionName": "Example Hospital",
                    "InstitutionalDepartmentName": "Radiology",
                    "RepetitionTime": 2.0,
                    "EchoTime": 0.03,
                    "FlipAngle": 77,
                    "SliceTiming": [0.0, 0.5, 1.0, 1.5],
                    "NumberOfVolumes": 300 if task == "rest" else 200,
                    "VoxelSize": [2.0, 2.0, 2.0],
                    "ConversionSoftware": "dcm2niix",
                    "ConversionSoftwareVersion": "v1.0.20220720",
                }

                with open(json_file, "w") as f:
                    json.dump(func_metadata, f, indent=2)

    return str(dataset_path)
