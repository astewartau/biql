---
layout: default
title: CLI Reference
nav_order: 4
description: "Complete reference for the biql command-line tool"
---

# CLI Reference

Complete reference for the `biql` command-line tool.

## Usage

```bash
biql [OPTIONS] QUERY
```

## Arguments

### QUERY
The BQL query string to execute. Can be quoted or unquoted:

```bash
# Simple queries (no quotes needed)
biql sub=01

# Complex queries (quotes recommended)
biql "SELECT sub, task WHERE datatype=func"

# Queries with special characters (quotes required)
biql "SELECT sub WHERE task LIKE '%back%'"
```

## Options

### Dataset Options

#### `--dataset PATH`, `-d PATH`
Specify the BIDS dataset directory path.

```bash
biql --dataset /path/to/bids "sub=01"
biql -d /data/study "SELECT DISTINCT task"
```

**Default**: Current working directory (`.`)

### Output Format Options

#### `--format FORMAT`, `-f FORMAT`
Specify the output format. Available formats:

- `json` (default) - JSON array of objects
- `table` - Pretty-printed table
- `csv` - Comma-separated values
- `tsv` - Tab-separated values  
- `paths` - File paths only (one per line)

```bash
biql "sub=01" --format table
biql "datatype=func" --format csv
biql "suffix=T1w" --format paths
```

#### `--output FILE`, `-o FILE`
Write output to file instead of stdout.

```bash
biql "datatype=func" --format csv --output functional_files.csv
biql "suffix=T1w" --format paths --output t1w_paths.txt
```

### Query Options

#### `--validate`, `-v`
Validate query syntax without executing. Useful for testing complex queries.

```bash
biql --validate "SELECT sub, COUNT(*) GROUP BY sub"
```

**Output**: 
- Success: `Query syntax is valid`
- Error: Detailed syntax error with position

#### `--validate-only`
Extended validation that checks query syntax and returns appropriate exit codes without execution.

```bash
biql --validate-only "SELECT sub WHERE datatype=func"
echo $?  # 0 for valid syntax, 1 for invalid
```

**Use case**: Automated syntax checking in scripts or CI/CD pipelines.

#### `--explain`
Show query execution plan without running the query.

```bash
biql --explain "SELECT sub WHERE datatype=func GROUP BY sub"
```

### Information Options

#### `--show-stats`
Display dataset statistics along with query results.

```bash
biql --show-stats "SELECT COUNT(*)"
```

**Output includes**:
- Total files in dataset
- Number of subjects/sessions
- Available datatypes
- Execution time

#### `--show-entities`
List all available BIDS entities in the dataset.

```bash
biql --show-entities ""
```

**Example output**:
```
Available entities in dataset:
- sub: 01, 02, 03, ...
- ses: 1, 2, baseline, followup
- task: rest, nback, faces
- datatype: anat, func, dwi
- suffix: T1w, bold, dwi, ...
```

### Debug Options

#### `--debug`
Enable verbose debug output showing query parsing and execution steps.

```bash
biql --debug "SELECT sub WHERE task=rest"
```

**Debug output includes**:
- Token parsing steps
- AST structure
- File filtering process
- Execution timing

#### `--profile`
Profile query execution and show performance metrics including memory usage and timing.

```bash
biql --profile "SELECT sub, COUNT(*) GROUP BY sub"
```

**Output includes**:
- Query execution time
- Memory usage (peak and current)
- File processing statistics
- Performance bottleneck identification

**Performance Expectations**:
- Memory usage stays under 500MB for datasets with <10,000 files
- Query time scales linearly with file count
- GROUP BY operations may use additional memory for aggregation

### Help Options

#### `--help`, `-h`
Show help message and exit.

#### `--version`
Show version information and exit.

## Query Examples by CLI Usage

### Basic File Discovery

```bash
# Find all files for a subject
biql "sub=01"

# Find functional scans
biql "datatype=func"

# Find specific task data
biql "task=nback AND datatype=func"
```

### Data Export Workflows

```bash
# Export functional file list for processing
biql "datatype=func" --format paths --output func_files.txt

# Create CSV of all scans with metadata
biql "SELECT sub, ses, task, filepath, metadata.RepetitionTime" \
     --format csv --output scan_list.csv

# Generate subject summary table
biql "SELECT sub, COUNT(*) as total_files GROUP BY sub" \
     --format table
```

### Quality Control

```bash
# Check dataset completeness
biql "SELECT sub, ses, COUNT(*) GROUP BY sub, ses" \
     --format table --show-stats

# Find missing data
biql "SELECT sub WHERE NOT task=rest" --format table

# Validate all files exist
biql "SELECT filepath WHERE NOT filepath" --format table
```

### Multi-format Output

```bash
# JSON for scripts
biql "sub=01" --format json > subject_01.json

# Table for humans
biql "SELECT datatype, COUNT(*) GROUP BY datatype" --format table

# CSV for spreadsheets
biql "participants.age<30" --format csv --output young_participants.csv

# Paths for shell scripts
biql "suffix=T1w" --format paths | while read file; do
    echo "Processing: $file"
done
```

## Advanced CLI Patterns

### Pipeline Integration

```bash
# Generate file lists for FSL
biql "datatype=func AND task=rest" --format paths > fsl_inputs.txt

# Create BIDS apps input
biql "SELECT sub FROM participants.group=control" \
     --format json > control_subjects.json

# Export for custom processing
biql "SELECT sub, ses, echo, part, filepath WHERE suffix=MEGRE" \
     --format csv > qsm_reconstruction_groups.csv
```

### Dataset Validation

```bash
# Check BIDS compliance
biql --show-entities "" | grep -q "required_field" || echo "Missing required entity"

# Validate metadata
biql "metadata.RepetitionTime" --show-stats

# Check for duplicates
biql "SELECT filename, COUNT(*) GROUP BY filename HAVING COUNT(*) > 1" \
     --format table
```

### Batch Processing

```bash
#!/bin/bash
# Process each subject separately
for subject in $(biql "SELECT DISTINCT sub" --format json | jq -r '.[].sub'); do
    echo "Processing subject $subject"
    biql "sub=$subject AND datatype=func" --format paths > "sub-${subject}_func.txt"
done
```

### Complex Query Building

```bash
# Build queries incrementally
biql --validate "SELECT sub"
biql --validate "SELECT sub WHERE datatype=func"  
biql --validate "SELECT sub WHERE datatype=func GROUP BY sub"
biql "SELECT sub WHERE datatype=func GROUP BY sub" --format table
```

## Error Handling

### Common Error Messages

#### Syntax Errors
```bash
$ biql "SELECT WHERE datatype=func"
Error: Expected field list after SELECT at position 7
       SELECT WHERE datatype=func
              ^
```

#### Dataset Errors
```bash
$ biql --dataset /nonexistent "sub=01"
Error: Dataset directory '/nonexistent' does not exist or is not accessible
```

#### File Output Errors
```bash
$ biql "sub=01" --output /root/file.csv
Error: Cannot write to '/root/file.csv': Permission denied
```

### Error Exit Codes

- `0` - Success
- `1` - Query syntax error
- `2` - Dataset loading error  
- `3` - Output file error
- `4` - Invalid command line arguments

## Configuration

### Environment Variables

#### `BIQL_DATASET_PATH`
Default dataset path when `--dataset` is not specified.

```bash
export BIQL_DATASET_PATH=/data/my_study
biql "sub=01"  # Uses /data/my_study automatically
```

#### `BIQL_OUTPUT_FORMAT`
Default output format when `--format` is not specified.

```bash
export BIQL_OUTPUT_FORMAT=table
biql "SELECT datatype, COUNT(*) GROUP BY datatype"  # Uses table format
```

### Shell Integration

#### Bash Completion
Add to `.bashrc` for tab completion:

```bash
eval "$(biql --completion bash)"
```

#### Command Aliases
Useful aliases for common operations:

```bash
alias bsub='biql "SELECT DISTINCT sub"'
alias btask='biql "SELECT DISTINCT task WHERE datatype=func"'
alias bfunc='biql "datatype=func" --format paths'
alias bstats='biql --show-stats ""'
```

## Performance Tips

### Query Optimization

1. **Use specific filters early**:
   ```bash
   # Good: Filter by subject first
   biql "sub=01 AND datatype=func"
   
   # Less efficient: Complex conditions first
   biql "metadata.RepetitionTime>2.0 AND sub=01"
   ```

2. **Limit output fields**:
   ```bash
   # Good: Select only needed fields
   biql "SELECT sub, filepath WHERE datatype=func"
   
   # Wasteful: Select everything
   biql "SELECT * WHERE datatype=func"
   ```

3. **Use DISTINCT for exploration**:
   ```bash
   # Fast: Get unique values
   biql "SELECT DISTINCT task"
   
   # Slower: Group and count
   biql "SELECT task, COUNT(*) GROUP BY task"
   ```

### Large Dataset Handling

For datasets with thousands of files:

```bash
# Profile query performance
biql --profile "complex query"

# Use paths format for minimal memory
biql "large query" --format paths --output results.txt

# Process in batches
for sub in $(biql "SELECT DISTINCT sub" --format json | jq -r '.[].sub'); do
    biql "sub=$sub AND datatype=func" --format paths >> "batch_${sub}.txt"
done
```

### Concurrent Query Support

BQL supports multiple simultaneous queries safely:

```bash
# Run multiple queries in parallel
biql "datatype=anat" --format paths > anat_files.txt &
biql "datatype=func" --format paths > func_files.txt &
biql "datatype=dwi" --format paths > dwi_files.txt &
wait
```

**Thread Safety**: All query operations are thread-safe and can run concurrently without data corruption.

## Troubleshooting

### Common Issues

#### Query Not Finding Files
```bash
# Debug what files are available
biql --show-entities ""

# Check your filter conditions
biql --debug "your query here"

# Verify dataset path
biql --show-stats ""
```

#### Slow Query Performance
```bash
# Profile the query
biql --profile "slow query"

# Simplify and test incrementally
biql "simplified version"
```

#### Output Format Issues
```bash
# Validate the query first
biql --validate "your query"

# Check for null values that break formatting
biql "your query" --debug
```

Continue to [Examples](examples.html) for real-world query patterns and cookbook recipes.