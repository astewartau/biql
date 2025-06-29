#!/usr/bin/env python3
"""
QSM-specific BIQL Examples

Demonstrates BIQL queries tailored for QSM (Quantitative Susceptibility Mapping) datasets
based on QSMxT requirements.
"""

import json
import os
import tempfile
from pathlib import Path

from biql import BIDSDataset, BIQLEvaluator, BIQLFormatter, BIQLParser


def create_qsm_test_dataset():
    """Create a test QSM dataset structure matching QSMxT examples"""

    # Create temporary directory structure
    temp_dir = Path(tempfile.mkdtemp())

    # Create BIDS structure matching QSMxT examples
    structures = [
        # Single echo T2*w
        "sub-1/anat/sub-1_part-mag_T2starw.nii",
        "sub-1/anat/sub-1_part-mag_T2starw.json",
        "sub-1/anat/sub-1_part-phase_T2starw.nii",
        "sub-1/anat/sub-1_part-phase_T2starw.json",
        "sub-1/anat/sub-1_T1w.nii",
        "sub-1/anat/sub-1_T1w.json",
        # Multi-echo MEGRE
        "sub-2/anat/sub-2_echo-1_part-mag_MEGRE.nii",
        "sub-2/anat/sub-2_echo-1_part-mag_MEGRE.json",
        "sub-2/anat/sub-2_echo-1_part-phase_MEGRE.nii",
        "sub-2/anat/sub-2_echo-1_part-phase_MEGRE.json",
        "sub-2/anat/sub-2_echo-2_part-mag_MEGRE.nii",
        "sub-2/anat/sub-2_echo-2_part-mag_MEGRE.json",
        "sub-2/anat/sub-2_echo-2_part-phase_MEGRE.nii",
        "sub-2/anat/sub-2_echo-2_part-phase_MEGRE.json",
        # Multiple acquisitions and runs
        "sub-3/anat/sub-3_acq-mygrea_run-1_echo-1_part-mag_MEGRE.nii",
        "sub-3/anat/sub-3_acq-mygrea_run-1_echo-1_part-mag_MEGRE.json",
        "sub-3/anat/sub-3_acq-mygrea_run-1_echo-1_part-phase_MEGRE.nii",
        "sub-3/anat/sub-3_acq-mygrea_run-1_echo-1_part-phase_MEGRE.json",
        "sub-3/anat/sub-3_acq-mygrea_run-1_echo-2_part-mag_MEGRE.nii",
        "sub-3/anat/sub-3_acq-mygrea_run-1_echo-2_part-mag_MEGRE.json",
        "sub-3/anat/sub-3_acq-mygrea_run-1_echo-2_part-phase_MEGRE.nii",
        "sub-3/anat/sub-3_acq-mygrea_run-1_echo-2_part-phase_MEGRE.json",
        "sub-3/anat/sub-3_acq-mygreb_run-1_echo-1_part-mag_MEGRE.nii",
        "sub-3/anat/sub-3_acq-mygreb_run-1_echo-1_part-mag_MEGRE.json",
        "sub-3/anat/sub-3_acq-mygreb_run-1_echo-1_part-phase_MEGRE.nii",
        "sub-3/anat/sub-3_acq-mygreb_run-1_echo-1_part-phase_MEGRE.json",
        # Multiple sessions
        "sub-4/ses-20231020/anat/sub-4_ses-20231020_part-mag_T2starw.nii",
        "sub-4/ses-20231020/anat/sub-4_ses-20231020_part-mag_T2starw.json",
        "sub-4/ses-20231020/anat/sub-4_ses-20231020_part-phase_T2starw.nii",
        "sub-4/ses-20231020/anat/sub-4_ses-20231020_part-phase_T2starw.json",
        "sub-4/ses-20231025/anat/sub-4_ses-20231025_echo-1_part-mag_MEGRE.nii",
        "sub-4/ses-20231025/anat/sub-4_ses-20231025_echo-1_part-mag_MEGRE.json",
        "sub-4/ses-20231025/anat/sub-4_ses-20231025_echo-1_part-phase_MEGRE.nii",
        "sub-4/ses-20231025/anat/sub-4_ses-20231025_echo-1_part-phase_MEGRE.json",
        "sub-4/ses-20231025/anat/sub-4_ses-20231025_echo-2_part-mag_MEGRE.nii",
        "sub-4/ses-20231025/anat/sub-4_ses-20231025_echo-2_part-mag_MEGRE.json",
        "sub-4/ses-20231025/anat/sub-4_ses-20231025_echo-2_part-phase_MEGRE.nii",
        "sub-4/ses-20231025/anat/sub-4_ses-20231025_echo-2_part-phase_MEGRE.json",
        # Derivatives (masks)
        "derivatives/qsm-forward/sub-1/anat/sub-1_mask.nii",
        "derivatives/qsm-forward/sub-2/anat/sub-2_mask.nii",
    ]

    # Create dataset_description.json
    desc = {
        "Name": "QSM Test Dataset",
        "BIDSVersion": "1.8.0",
        "Description": "Test dataset for QSM processing with QSMxT",
    }

    with open(temp_dir / "dataset_description.json", "w") as f:
        json.dump(desc, f, indent=2)

    # Create all files and directories
    for structure in structures:
        file_path = temp_dir / structure
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if structure.endswith(".json"):
            # Create basic JSON metadata
            metadata = {
                "EchoTime": (
                    0.01
                    if "echo-1" in structure
                    else 0.02 if "echo-2" in structure else 0.015
                ),
                "MagneticFieldStrength": 3.0,
                "Manufacturer": "Siemens",
            }
            with open(file_path, "w") as f:
                json.dump(metadata, f, indent=2)
        else:
            # Create empty nii files
            file_path.touch()

    return temp_dir


def main():
    """Run QSM-specific BIQL examples"""

    print("Creating QSM test dataset...")
    dataset_path = create_qsm_test_dataset()

    try:
        print(f"Loading dataset from: {dataset_path}")
        dataset = BIDSDataset(dataset_path)
        evaluator = BIQLEvaluator(dataset)

        print(f"Dataset loaded: {len(dataset.files)} files indexed")
        print()

        # QSM-specific BIQL queries replacing the BIDS parser functionality

        print("=== QSM Reconstruction Groups (equivalent to your BIDS parser) ===")
        print()

        # 1. Find all QSM-relevant files (magnitude and phase)
        print("1. All QSM-relevant files (mag and phase parts):")
        parser = BIQLParser.from_string("part=mag OR part=phase")
        query = parser.parse()
        results = evaluator.evaluate(query)
        print(f"Found {len(results)} QSM files")

        # Group by reconstruction units
        print("\n2. Group QSM files by reconstruction units:")
        parser = BIQLParser.from_string(
            "SELECT sub, ses, acq, run, COUNT(*) "
            "WHERE (part=mag OR part=phase) AND (suffix=T2starw OR suffix=MEGRE) "
            "GROUP BY sub, ses, acq, run"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)

        print("QSM Reconstruction Groups:")
        formatted = BIQLFormatter.format(results, "table")
        print(formatted)
        print()

        # 3. Find specific acquisition types
        print("3. T2* single-echo acquisitions:")
        parser = BIQLParser.from_string("suffix=T2starw AND part=mag")
        query = parser.parse()
        results = evaluator.evaluate(query)

        for result in results[:5]:
            print(f"  {result['filename']}")
        print()

        print("4. Multi-echo MEGRE acquisitions:")
        parser = BIQLParser.from_string("suffix=MEGRE AND part=mag")
        query = parser.parse()
        results = evaluator.evaluate(query)

        for result in results[:5]:
            echo = result.get("echo", "N/A")
            print(f"  {result['filename']} (echo {echo})")
        print()

        # 4. Find magnitude-phase pairs for specific subjects
        print("5. Magnitude-phase pairs for subject 2:")
        parser = BIQLParser.from_string(
            "SELECT sub, echo, part, filename "
            "WHERE sub=2 AND (part=mag OR part=phase) "
            "ORDER BY echo, part"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)

        formatted = BIQLFormatter.format(results, "table")
        print(formatted)
        print()

        # 5. Advanced: Find complete QSM groups (both mag and phase present)
        print("6. Complete QSM reconstruction groups (both mag and phase present):")

        # This is more complex - we need to find groups where both mag and phase exist
        # First get all mag files
        parser = BIQLParser.from_string("part=mag AND (suffix=T2starw OR suffix=MEGRE)")
        query = parser.parse()
        mag_results = evaluator.evaluate(query)

        complete_groups = []
        for mag_file in mag_results:
            # Build corresponding phase query
            conditions = [f"part=phase"]
            if mag_file.get("sub"):
                conditions.append(f"sub={mag_file['sub']}")
            if mag_file.get("ses"):
                conditions.append(f"ses={mag_file['ses']}")
            if mag_file.get("acq"):
                conditions.append(f"acq={mag_file['acq']}")
            if mag_file.get("run"):
                conditions.append(f"run={mag_file['run']}")
            if mag_file.get("echo"):
                conditions.append(f"echo={mag_file['echo']}")
            if mag_file.get("suffix"):
                conditions.append(f"suffix={mag_file['suffix']}")

            phase_query = " AND ".join(conditions)
            parser = BIQLParser.from_string(phase_query)
            query = parser.parse()
            phase_results = evaluator.evaluate(query)

            if phase_results:
                group_id = f"sub-{mag_file['sub']}"
                if mag_file.get("ses"):
                    group_id += f"_ses-{mag_file['ses']}"
                if mag_file.get("acq"):
                    group_id += f"_acq-{mag_file['acq']}"
                if mag_file.get("run"):
                    group_id += f"_run-{mag_file['run']}"

                complete_groups.append(
                    {
                        "group_id": group_id,
                        "subject": mag_file["sub"],
                        "session": mag_file.get("ses"),
                        "acquisition": mag_file.get("acq"),
                        "run": mag_file.get("run"),
                        "suffix": mag_file["suffix"],
                        "mag_files": 1,
                        "phase_files": len(phase_results),
                    }
                )

        # Remove duplicates and show results
        seen = set()
        unique_groups = []
        for group in complete_groups:
            if group["group_id"] not in seen:
                seen.add(group["group_id"])
                unique_groups.append(group)

        print(f"Found {len(unique_groups)} complete QSM reconstruction groups:")
        formatted = BIQLFormatter.format(unique_groups, "table")
        print(formatted)
        print()

        # 6. Find derivatives/masks
        print("7. QSM processing derivatives (masks):")
        parser = BIQLParser.from_string("suffix=mask")
        query = parser.parse()
        results = evaluator.evaluate(query)

        if results:
            for result in results:
                print(f"  {result['filename']} for subject {result['sub']}")
        else:
            print("  No masks found")
        print()

        # 7. Complex query: Multi-echo acquisitions with specific parameters
        print("8. Multi-echo MEGRE with multiple acquisitions:")
        parser = BIQLParser.from_string(
            "SELECT sub, acq, echo, part, filename "
            "WHERE suffix=MEGRE AND acq~=/myg.*/ "
            "ORDER BY sub, acq, echo, part"
        )
        query = parser.parse()
        results = evaluator.evaluate(query)

        if results:
            formatted = BIQLFormatter.format(results, "table")
            print(formatted)
        else:
            print("  No multi-acquisition MEGRE found")
        print()

        # 8. Summary query equivalent to your parser's grouping logic
        print("9. QSM Group Summary (mimicking your parser's output):")
        print("   This shows the logical groups your parser would create:")

        # Get unique combinations of grouping variables
        parser = BIQLParser.from_string(
            "SELECT sub, ses, acq, run, suffix "
            "WHERE (part=mag OR part=phase) AND (suffix=T2starw OR suffix=MEGRE) "
            "GROUP BY sub, ses, acq, run, suffix"
        )
        query = parser.parse()
        group_summary = evaluator.evaluate(query)

        for i, group in enumerate(group_summary, 1):
            print(f"\n   Group {i}:")
            print(f"     Subject: {group['sub']}")
            print(f"     Session: {group.get('ses', 'None')}")
            print(f"     Acquisition: {group.get('acq', 'None')}")
            print(f"     Run: {group.get('run', 'None')}")
            print(f"     Suffix: {group['suffix']}")
            print(f"     Files in group: {group['count']}")

            # Show what files are in this group
            conditions = [f"sub={group['sub']}"]
            if group.get("ses"):
                conditions.append(f"ses={group['ses']}")
            if group.get("acq"):
                conditions.append(f"acq={group['acq']}")
            if group.get("run"):
                conditions.append(f"run={group['run']}")
            conditions.append(f"suffix={group['suffix']}")
            conditions.append("(part=mag OR part=phase)")

            detail_query = " AND ".join(conditions)
            parser = BIQLParser.from_string(
                f"SELECT part, echo, filename WHERE {detail_query}"
            )
            query = parser.parse()
            detail_results = evaluator.evaluate(query)

            for detail in detail_results:
                echo_str = f" echo-{detail['echo']}" if detail.get("echo") else ""
                print(f"       {detail['part']}{echo_str}: {detail['filename']}")

    finally:
        # Clean up temporary directory
        import shutil

        shutil.rmtree(dataset_path)


if __name__ == "__main__":
    main()
