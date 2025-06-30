---
title: Language Reference
nav_order: 4
---

# BIQL Language Reference

BIQL (BIDS Query Language) is a SQL-like query language for querying Brain Imaging Data Structure (BIDS) datasets. This reference describes all language constructs, clauses, and operators.

## What BIQL Queries

BIQL queries operate on BIDS datasets, which are structured neuroimaging data repositories following the Brain Imaging Data Structure specification. When you query with BIQL, you're searching through:

### 1. BIDS Entities from Filenames

BIDS filenames encode metadata using key-value pairs separated by underscores. For example:
```
sub-01_ses-pre_task-rest_run-1_bold.nii.gz
```

From this filename, BIQL extracts:
- `sub` = "01" (subject identifier)
- `ses` = "pre" (session identifier)
- `task` = "rest" (task name)
- `run` = "1" (run number)
- `suffix` = "bold" (file type suffix)
- `datatype` = "func" (from parent directory)

Common BIDS entities include:
- `sub` - Subject identifier
- `ses` - Session identifier
- `task` - Task name
- `run` - Run number
- `acq` - Acquisition label
- `ce` - Contrast enhancing agent
- `rec` - Reconstruction label
- `dir` - Phase encoding direction
- `echo` - Echo number
- `part` - Part label (e.g., mag, phase)
- `space` - Spatial reference
- `res` - Resolution
- `den` - Density
- `label` - Label or atlas name
- `desc` - Description

The complete list of entities is defined in the [BIDS specification](https://bids-specification.readthedocs.io/).

### 2. JSON Sidecar Metadata

BIDS datasets include JSON sidecar files that contain additional metadata. BIQL makes these accessible through the `metadata` namespace:

```sql
WHERE metadata.EchoTime < 0.005
WHERE metadata.RepetitionTime = 2.0
SELECT metadata.MagneticFieldStrength, metadata.ManufacturerModelName
```

Common metadata fields include:
- `RepetitionTime` (TR)
- `EchoTime` (TE)
- `FlipAngle`
- `SliceTiming`
- `PhaseEncodingDirection`
- `MagneticFieldStrength`
- `Manufacturer`
- `ManufacturerModelName`
- `SequenceName`

The metadata follows BIDS inheritance principle: metadata defined at higher levels (e.g., dataset or subject level) applies to all applicable files below unless overridden.

### 3. Participants Information

The `participants.tsv` file contains subject-level information. BIQL makes these accessible through the `participants` namespace:

```sql
WHERE participants.age > 18
SELECT sub, participants.sex, participants.handedness
```

Common participants fields include:
- `age`
- `sex`
- `handedness`
- `group`
- Any custom columns defined in your participants.tsv file

### 4. Computed Fields

BIQL also provides computed fields for convenience:
- `filename` - Just the file name
- `filepath` - Full absolute path to the file
- `relative_path` - Path relative to dataset root
- `extension` - File extension (e.g., ".nii.gz")

## Query Structure

BIQL queries follow a SQL-like structure:

```sql
SELECT fields
WHERE conditions
GROUP BY fields
HAVING aggregate_conditions
ORDER BY fields [ASC|DESC]
FORMAT output_type
```

Minimal queries can be just conditions:
```sql
sub=01
```

## Clauses

### SELECT

Specifies which fields to return in the result set.

```sql
SELECT sub, ses, task, filepath
```

### WHERE

Filters data based on conditions.

```sql
WHERE datatype=func AND task=rest
```

### GROUP BY

Groups results by specified fields.

```sql
GROUP BY sub, ses
```

### HAVING

Filters grouped results based on aggregate conditions.

```sql
HAVING COUNT(*) > 10
```

### ORDER BY

Sorts results by specified fields in ascending (ASC) or descending (DESC) order.

```sql
ORDER BY sub ASC, task DESC
```

### FORMAT

Specifies the output format for results.

```sql
FORMAT json
```

## Keywords

### DISTINCT

Returns only unique values.

```sql
SELECT DISTINCT task
```

### AS

Creates aliases for fields or expressions.

```sql
SELECT COUNT(*) AS file_count
```

### AND, OR, NOT

Logical operators for combining conditions.

```sql
WHERE datatype=func AND (task=rest OR task=nback)
WHERE NOT suffix=events
```

### IN

Tests if a value is within a list.

```sql
WHERE task IN [rest, nback, flanker]
```

## Operators

### Comparison Operators

- `=` or `==` - Equality
- `!=` - Not equal
- `>` - Greater than
- `<` - Less than
- `>=` - Greater than or equal
- `<=` - Less than or equal

```sql
WHERE run > 2
WHERE metadata.RepetitionTime <= 3.0
```

### Pattern Matching Operator

- `~=` - Regular expression match

```sql
WHERE task~=/.*back.*/
```

### Range Operator

Specifies a range of values using `[start:end]` syntax.

```sql
WHERE run=[1:5]
```

## Aggregate Functions

### COUNT

Counts records or non-null values.

```sql
SELECT COUNT(*) AS total_files
SELECT COUNT(ses) AS sessions_with_data
```

### AVG

Calculates the average of numeric values.

```sql
SELECT AVG(metadata.RepetitionTime) AS avg_tr
```

### MAX

Returns the maximum value.

```sql
SELECT MAX(run) AS max_run
```

### MIN

Returns the minimum value.

```sql
SELECT MIN(metadata.EchoTime) AS min_echo_time
```

### SUM

Calculates the sum of numeric values.

```sql
SELECT SUM(metadata.NumberOfVolumes) AS total_volumes
```

### ARRAY_AGG

Collects values into an array, optionally with conditions.

```sql
SELECT ARRAY_AGG(filename) AS all_files
SELECT ARRAY_AGG(filename WHERE part='mag') AS magnitude_files
```

## Field Types

### BIDS Entities

Standard BIDS entities can be queried directly:

- `sub` - Subject identifier
- `ses` - Session identifier
- `task` - Task name
- `run` - Run number
- `acq` - Acquisition label
- `datatype` - Data type (func, anat, dwi, etc.)
- `suffix` - File suffix (T1w, bold, events, etc.)
- `part` - Part label (mag, phase for multi-part data)
- `echo` - Echo number

```sql
WHERE sub=01 AND ses=pre AND task=rest
```

### Computed Fields

- `filename` - Just the file name
- `filepath` - Full file path
- `relative_path` - Path relative to dataset root

```sql
SELECT filename, filepath
```

### Nested Access

Access metadata from JSON sidecars or participants.tsv:

- `metadata.FieldName` - Access JSON sidecar fields
- `participants.FieldName` - Access participants.tsv columns

```sql
WHERE metadata.RepetitionTime < 2.0
SELECT participants.age, participants.sex
```

## Pattern Matching

### Wildcards

- `*` - Matches any sequence of characters
- `?` - Matches single character

```sql
WHERE suffix=*bold*
WHERE task=?back
```

### Regular Expressions

Use the `~=` operator with regex patterns in string literals:

```sql
WHERE suffix~="T[12]w"
WHERE task~="rest|task"
```

## Data Types

BIQL takes a flexible approach to data types, automatically handling type conversions based on context. This makes queries more intuitive and forgiving of different data representations.

### Strings

Enclosed in single or double quotes:

```sql
WHERE task='rest' OR task="n-back"
```

### Numbers

Integer or floating-point values:

```sql
WHERE run=1
WHERE metadata.RepetitionTime=2.5
```

### Flexible Value Matching

BIQL intelligently matches values regardless of their representation:

- Leading zeros are handled automatically: `sub=01` matches `sub=1` and `sub=001`
- String and numeric comparisons work interchangeably: `run=1` matches `run='1'`
- The comparison adapts to the context:
  - For BIDS entities that are typically zero-padded (like `sub-01`), queries work with or without padding
  - For numeric metadata fields, string representations are converted appropriately

Examples:
```sql
WHERE sub=1        # Matches sub-01, sub-001, etc.
WHERE sub=01       # Also matches sub-1, sub-01, sub-001
WHERE run='2'      # Matches run-2, run-02
WHERE echo=1       # Matches echo-1, echo-01
```

### Lists

Comma-separated values in square brackets:

```sql
WHERE task IN [rest, nback, flanker]
WHERE sub IN [1, 2, 3]    # Matches sub-01, sub-02, sub-03
```

### Ranges

Start and end values in square brackets with colon:

```sql
WHERE run=[1:5]      # Matches run-1 through run-5 (including run-01, etc.)
WHERE echo=[1:3]     # Matches echo-1, echo-2, echo-3
```

## Output Formats

Available output formats for the FORMAT clause:

- `json` - JSON format (default)
- `table` - ASCII table
- `csv` - Comma-separated values
- `tsv` - Tab-separated values
- `paths` - Just file paths
- `dataframe` - Pandas DataFrame (Python API only)

```sql
FORMAT table
FORMAT csv
```

## Special Features

### Implicit AND

Adjacent conditions without explicit AND are treated as AND:

```sql
subject=01 task=rest
-- Equivalent to:
subject=01 AND task=rest
```

### Comments

Lines starting with `#` are treated as comments:

```sql
# This query finds all functional data
WHERE datatype=func
```

### Case Sensitivity

- Keywords are case-insensitive: `SELECT`, `select`, `Select` are equivalent
- Entity values preserve case: `task=Rest` is different from `task=rest`

### Flexible Identifiers

Identifiers can contain hyphens:

```sql
WHERE task=n-back
```
