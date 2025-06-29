#!/bin/bash
"""
CLI Examples for BIDS Query Language (BIQL)

Demonstrates command-line usage of biql with various query types.
"""

# Set the dataset path - adjust this to point to your BIDS dataset
DATASET="/home/ashley/repos/bids-examples/synthetic"

echo "=== BIQL CLI Examples ==="
echo "Dataset: $DATASET"
echo

# Check if dataset exists
if [ ! -d "$DATASET" ]; then
    echo "Error: Dataset not found at $DATASET"
    echo "Please adjust the DATASET variable in this script"
    exit 1
fi

echo "=== Dataset Information ==="
echo "Show dataset statistics:"
biql --dataset "$DATASET" --show-stats "sub=01"
echo

echo "Show available entities:"
biql --dataset "$DATASET" --show-entities "sub=01"
echo

echo "=== Basic Queries ==="

echo "1. Find all files for subject 01:"
biql --dataset "$DATASET" "sub=01" | jq length
echo

echo "2. Find all functional files:"
biql --dataset "$DATASET" "datatype=func" --format table | head -10
echo

echo "3. Find T1w anatomical files:"
biql --dataset "$DATASET" "datatype=anat AND suffix=T1w" --format paths
echo

echo "=== Logical Operators ==="

echo "4. AND operator - functional files for subject 01:"
biql --dataset "$DATASET" "sub=01 AND datatype=func" | jq '.[].filename'
echo

echo "5. OR operator - nback or rest tasks:"
biql --dataset "$DATASET" "task=nback OR task=rest" | jq 'group_by(.task) | map({task: .[0].task, count: length})'
echo

echo "6. NOT operator - non-anatomical files:"
biql --dataset "$DATASET" "NOT datatype=anat" | jq 'group_by(.datatype) | map({datatype: .[0].datatype, count: length})'
echo

echo "=== Pattern Matching ==="

echo "7. Wildcard matching - files with 'bold' in suffix:"
biql --dataset "$DATASET" "suffix=*bold*" | jq length
echo

echo "8. Regular expression matching - subjects 01-03:"
biql --dataset "$DATASET" "sub~=/0[1-3]/" | jq 'group_by(.sub) | map({sub: .[0].sub, count: length})'
echo

echo "=== Range Queries ==="

echo "9. Range query - runs 1-2:"
biql --dataset "$DATASET" "run=[1:2]" | jq 'map(select(.run != null)) | group_by(.run) | map({run: .[0].run, count: length})'
echo

echo "=== SELECT Queries ==="

echo "10. Select specific fields:"
biql --dataset "$DATASET" "SELECT sub, task, run, filepath WHERE datatype=func" --format table | head -10
echo

echo "11. Select with aliases:"
biql --dataset "$DATASET" "SELECT sub AS subject, task AS paradigm WHERE datatype=func" | head -3 | jq
echo

echo "=== Aggregation ==="

echo "12. Count files by subject:"
biql --dataset "$DATASET" "SELECT sub, COUNT(*) GROUP BY sub" --format table
echo

echo "13. Count files by datatype:"
biql --dataset "$DATASET" "SELECT datatype, COUNT(*) GROUP BY datatype" --format table
echo

echo "=== Metadata Queries ==="

echo "14. Files with RepetitionTime metadata:"
biql --dataset "$DATASET" "metadata.RepetitionTime>0" | jq 'map(select(.metadata.RepetitionTime != null)) | length'
echo

echo "15. Specific RepetitionTime values:"
biql --dataset "$DATASET" "SELECT task, metadata.RepetitionTime WHERE metadata.RepetitionTime>0" | jq 'map(select(.["metadata.RepetitionTime"] != null))'
echo

echo "=== Participant Data ==="

echo "16. Files for participants over 25:"
biql --dataset "$DATASET" "participants.age>25" | jq 'group_by(.sub) | map({sub: .[0].sub, count: length})'
echo

echo "17. Files by participant sex:"
biql --dataset "$DATASET" "SELECT sub, participants.sex WHERE participants.sex!=null" | jq 'group_by(.["participants.sex"]) | map({sex: .[0]["participants.sex"], subjects: [.[].sub] | unique})'
echo

echo "=== Ordering ==="

echo "18. Order by subject and run:"
biql --dataset "$DATASET" "datatype=func ORDER BY sub, run" --format table | head -10
echo

echo "19. Order by task descending:"
biql --dataset "$DATASET" "datatype=func ORDER BY task DESC" | jq 'map(.task)' | head -10
echo

echo "=== Complex Queries ==="

echo "20. Complex query with multiple conditions:"
biql --dataset "$DATASET" "SELECT sub, ses, task, run WHERE (datatype=func OR datatype=anat) AND (sub=01 OR sub=02) ORDER BY sub, datatype, task" --format table
echo

echo "21. Query with grouping and having (conceptual):"
biql --dataset "$DATASET" "SELECT task, COUNT(*) GROUP BY task" --format table
echo

echo "=== Output Formats ==="

echo "22. JSON format (default):"
biql --dataset "$DATASET" "sub=01 AND datatype=anat" | jq 'map({subject: .sub, file: .filename})'
echo

echo "23. Table format:"
biql --dataset "$DATASET" "sub=01 AND datatype=anat" --format table
echo

echo "24. CSV format:"
biql --dataset "$DATASET" "sub=01 AND datatype=anat" --format csv | head -5
echo

echo "25. Paths only:"
biql --dataset "$DATASET" "sub=01 AND datatype=anat" --format paths
echo

echo "=== Query Validation ==="

echo "26. Validate query syntax (valid):"
biql --dataset "$DATASET" --validate-only "sub=01 AND datatype=func"
echo

echo "27. Validate query syntax (invalid):"
biql --dataset "$DATASET" --validate-only "SELECT FROM WHERE" || echo "Query validation failed as expected"
echo

echo "=== Advanced Examples ==="

echo "28. Find sessions with both anatomical and functional data:"
biql --dataset "$DATASET" "SELECT sub, ses WHERE datatype=anat" | jq '[.[].sub + "_" + (.ses // "nosession")] | unique' > /tmp/anat_sessions.txt
biql --dataset "$DATASET" "SELECT sub, ses WHERE datatype=func" | jq '[.[].sub + "_" + (.ses // "nosession")] | unique' > /tmp/func_sessions.txt
echo "Sessions with both anat and func:"
comm -12 <(sort /tmp/anat_sessions.txt) <(sort /tmp/func_sessions.txt) | jq -r
rm -f /tmp/anat_sessions.txt /tmp/func_sessions.txt
echo

echo "29. Export query results to file:"
biql --dataset "$DATASET" "datatype=func" --output /tmp/functional_files.json
echo "Exported $(jq length /tmp/functional_files.json) functional files to /tmp/functional_files.json"
rm -f /tmp/functional_files.json
echo

echo "30. Debug mode for troubleshooting:"
biql --dataset "$DATASET" --debug "sub=01" | head -5
echo

echo "=== All examples completed ==="
