#!/usr/bin/env python3
"""
Basic BIQL Examples

Demonstrates basic usage of the BIDS Query Language Python API.
"""

from pathlib import Path

from biql import BIDSDataset, BIQLEvaluator, BIQLFormatter, BIQLParser

# Example dataset path (adjust to your dataset)
# Note: This example expects a BIDS dataset. You can download bids-examples or use your own dataset.
DATASET_PATH = Path("path/to/your/bids/dataset")


def main():
    """Run basic BIQL examples"""

    if not DATASET_PATH.exists():
        print(f"Dataset not found at {DATASET_PATH}")
        print(
            "Please adjust DATASET_PATH in this script to point to a valid BIDS dataset"
        )
        return

    print("Loading BIDS dataset...")
    dataset = BIDSDataset(DATASET_PATH)
    evaluator = BIQLEvaluator(dataset)

    print(f"Dataset loaded: {len(dataset.files)} files indexed")
    print(f"Subjects: {sorted(dataset.get_subjects())}")
    print(f"Data types: {sorted(dataset.get_datatypes())}")
    print()

    # Example 1: Simple entity query
    print("=== Example 1: Find all files for subject 01 ===")
    parser = BIQLParser.from_string("sub=01")
    query = parser.parse()
    results = evaluator.evaluate(query)

    print(f"Found {len(results)} files for subject 01")
    for result in results[:3]:  # Show first 3
        print(f"  {result['filename']}")
    if len(results) > 3:
        print(f"  ... and {len(results) - 3} more")
    print()

    # Example 2: Datatype filtering
    print("=== Example 2: Find all functional files ===")
    parser = BIQLParser.from_string("datatype=func")
    query = parser.parse()
    results = evaluator.evaluate(query)

    print(f"Found {len(results)} functional files")
    tasks = set(r.get("task", "unknown") for r in results)
    print(f"Tasks found: {sorted(tasks)}")
    print()

    # Example 3: Logical operators
    print("=== Example 3: Find T1w anatomical files ===")
    parser = BIQLParser.from_string("datatype=anat AND suffix=T1w")
    query = parser.parse()
    results = evaluator.evaluate(query)

    print(f"Found {len(results)} T1w files")
    for result in results:
        print(f"  {result['sub']}: {result['filename']}")
    print()

    # Example 4: SELECT specific fields
    print("=== Example 4: Select specific fields ===")
    parser = BIQLParser.from_string(
        "SELECT sub, task, run, filepath WHERE datatype=func"
    )
    query = parser.parse()
    results = evaluator.evaluate(query)

    print("Functional files (sub, task, run):")
    formatted = BIQLFormatter.format(results[:5], "table")  # Show first 5 as table
    print(formatted)
    print()

    # Example 5: Grouping and counting
    print("=== Example 5: Count files by subject ===")
    parser = BIQLParser.from_string("SELECT sub, COUNT(*) GROUP BY sub")
    query = parser.parse()
    results = evaluator.evaluate(query)

    for result in results:
        print(f"  Subject {result['sub']}: {result['_count']} files")
    print()

    # Example 6: Pattern matching
    print("=== Example 6: Pattern matching ===")
    parser = BIQLParser.from_string('task~=".*back.*" OR suffix=*bold*')
    query = parser.parse()
    results = evaluator.evaluate(query)

    print(f"Found {len(results)} files matching pattern")
    for result in results[:3]:
        task = result.get("task", "N/A")
        suffix = result.get("suffix", "N/A")
        print(f"  {result['filename']} (task={task}, suffix={suffix})")
    print()

    # Example 7: Range queries
    print("=== Example 7: Range queries ===")
    parser = BIQLParser.from_string("run=[1:2] AND task=nback")
    query = parser.parse()
    results = evaluator.evaluate(query)

    print(f"Found {len(results)} nback files with run 1-2")
    for result in results:
        run = result.get("run", "N/A")
        print(f"  {result['sub']}: run {run}")
    print()

    # Example 8: Metadata queries (if available)
    print("=== Example 8: Metadata queries ===")
    parser = BIQLParser.from_string("metadata.RepetitionTime>0")
    query = parser.parse()
    results = evaluator.evaluate(query)

    print(f"Found {len(results)} files with RepetitionTime metadata")
    for result in results[:3]:
        tr = result.get("metadata", {}).get("RepetitionTime", "N/A")
        print(f"  {result['filename']}: TR = {tr}")
    print()

    # Example 9: Participant data queries (if available)
    print("=== Example 9: Participant data queries ===")
    parser = BIQLParser.from_string("participants.age>25")
    query = parser.parse()
    results = evaluator.evaluate(query)

    print(f"Found {len(results)} files for participants over 25")
    unique_subs = set(r.get("sub") for r in results)
    for sub in sorted(unique_subs):
        if sub in dataset.participants:
            age = dataset.participants[sub].get("age", "N/A")
            sex = dataset.participants[sub].get("sex", "N/A")
            print(f"  Subject {sub}: age {age}, sex {sex}")
    print()

    # Example 10: Complex query with ordering
    print("=== Example 10: Complex query with ordering ===")
    parser = BIQLParser.from_string(
        "SELECT sub, ses, task, run, filepath "
        "WHERE datatype=func AND (task=nback OR task=rest) "
        "ORDER BY sub, task, run"
    )
    query = parser.parse()
    results = evaluator.evaluate(query)

    print(f"Functional files (nback or rest), ordered:")
    formatted = BIQLFormatter.format(results[:10], "table")
    print(formatted)


if __name__ == "__main__":
    main()
