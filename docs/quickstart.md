# Quickstart Guide

Get up and running with BQL in 5 minutes! This guide will walk you through installation and your first queries.

## Installation

### Using pip (Recommended)

```bash
pip install biql
```

### Using conda

```bash
conda install -c conda-forge biql
```

### From Source

```bash
git clone https://github.com/user/biql.git
cd biql
pip install -e .
```

## Verify Installation

```bash
biql --version
biql --help
```

## Your First Query

Let's start with a simple query to explore your BIDS dataset:

```bash
# Navigate to your BIDS dataset
cd /path/to/your/bids/dataset

# Show all subjects
biql "SELECT DISTINCT sub"
```

**Expected Output:**
```
[
  {"sub": "01"},
  {"sub": "02"},
  {"sub": "03"}
]
```

## Basic Queries

### 1. Find All Functional Scans

```bash
biql "SELECT sub, ses, task, run, filename WHERE datatype=func"
```

### 2. Count Files by Datatype

```bash
biql "SELECT datatype, COUNT(*) GROUP BY datatype" --format table
```

**Output:**
```
| datatype | count |
|----------|-------|
| anat     | 15    |
| func     | 120   |
| dwi      | 30    |
```

### 3. Find Specific Task Data

```bash
biql "SELECT sub, run, filepath WHERE task=nback AND datatype=func"
```

### 4. Get Unique Tasks

```bash
biql "SELECT DISTINCT task WHERE datatype=func"
```

## Working with Different Output Formats

### JSON (Default)
```bash
biql "sub=01" 
```

### Table Format
```bash
biql "sub=01" --format table
```

### CSV Export
```bash
biql "datatype=func" --format csv --output results.csv
```

### File Paths Only
```bash
biql "task=rest" --format paths > rest_files.txt
```

## Practical Examples

### Dataset Overview

Get a quick overview of your dataset:

```bash
# Show dataset statistics
biql --show-stats "SELECT COUNT(*)"

# See all available entities
biql --show-entities ""
```

### Quality Control

Check for missing or inconsistent data:

```bash
# Find subjects with missing sessions
biql "SELECT sub, COUNT(DISTINCT ses) GROUP BY sub" --format table

# Check for incomplete task coverage
biql "SELECT sub, task, COUNT(*) WHERE datatype=func GROUP BY sub, task" --format table
```

### File Discovery for Processing

Generate file lists for processing pipelines:

```bash
# All T1w files for preprocessing
biql "suffix=T1w" --format paths > t1w_files.txt

# Functional files for specific subjects
biql "datatype=func AND sub IN [01, 02, 03]" --format csv --output func_subset.csv
```

## Advanced Patterns

### Pattern Matching

```bash
# Find files matching patterns
biql "suffix=*bold*"

# Regex matching for subject ranges
biql "sub~=\"0[1-5]\""

# Complex regex patterns for file discovery
biql "filename~=\".*ses-[0-9]+.*task-rest.*\""

# SQL-style LIKE patterns  
biql "task LIKE \"%back%\""
```

### Metadata Queries

```bash
# Find scans with specific parameters
biql "metadata.RepetitionTime>2.0"

# Group by acquisition parameters
biql "SELECT metadata.EchoTime, COUNT(*) GROUP BY metadata.EchoTime"
```

### Complex Filtering

```bash
# Multiple conditions
biql "SELECT sub, ses, task WHERE datatype=func AND (task=rest OR task=nback) AND run=[1:2]"

# Exclude specific data
biql "SELECT sub, filename WHERE NOT task=localizer"
```

## QSM Workflow Example

For Quantitative Susceptibility Mapping (QSM) workflows:

```bash
# Find QSM reconstruction groups
biql "SELECT sub, ses, acq, filename, COUNT(*) as files \
      WHERE (part=mag OR part=phase) AND suffix=MEGRE \
      GROUP BY sub, ses, acq" --format table

# Get complete magnitude/phase pairs
biql "SELECT sub, echo, part, filename \
      WHERE suffix=MEGRE AND sub=01 \
      ORDER BY echo, part" --format table
```

## Next Steps

Now that you've got the basics down, explore more advanced features:

- 📖 **[Language Reference](language.html)** - Complete BQL syntax guide
- ⚙️ **[CLI Reference](cli.html)** - All command-line options
- 🔬 **[Examples](examples.html)** - Real-world query cookbook
- 🧠 **[QSM Guide](qsm_migration_guide.html)** - Specialized QSM workflows

## Tips for Success

1. **Start Simple** - Begin with basic SELECT queries and add complexity gradually
2. **Use DISTINCT** - Great for exploring what entities/values are available
3. **Test Incrementally** - Build complex queries piece by piece
4. **Check Your Logic** - Use COUNT(*) to verify your filters are working correctly
5. **Save Useful Queries** - Keep a collection of your most-used patterns

## Getting Help

- **Built-in Help**: `biql --help`
- **Query Validation**: Use `--validate` flag to check syntax without running
- **Debug Mode**: Add `--debug` for detailed execution information
- **GitHub Issues**: [Report bugs or request features](https://github.com/user/biql/issues)

Ready to become a BQL expert? Continue with the [Language Reference](language.html)!