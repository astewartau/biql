---
layout: default
title: Language Reference
nav_order: 3
description: "Complete syntax guide and reference for the BIDS Query Language"
---

# BIQL Language Reference

Complete syntax guide and reference for the BIDS Query Language.

## Table of Contents

- [Query Structure](#query-structure)
- [SELECT Clause](#select-clause)
- [WHERE Clause](#where-clause)
- [GROUP BY and Aggregation](#group-by-and-aggregation)
- [HAVING Clause](#having-clause)
- [ORDER BY Clause](#order-by-clause)
- [DISTINCT](#distinct)
- [Operators](#operators)
- [Data Types](#data-types)
- [BIDS Entities](#bids-entities)
- [Metadata Access](#metadata-access)
- [Participant Data](#participant-data)

## Query Structure

BIQL queries follow a familiar SQL-like structure:

```sql
[SELECT [DISTINCT] field1, field2, ...]
[WHERE condition]
[GROUP BY field1, field2, ...]
[HAVING condition]
[ORDER BY field1 [ASC|DESC], field2 [ASC|DESC], ...]
[FORMAT output_format]
```

All clauses are optional. The simplest query is just a WHERE condition:

```sql
sub=01
```

## SELECT Clause

The SELECT clause specifies which fields to include in the output.

### Basic Field Selection

```sql
SELECT sub, ses, task, filename
```

### Wildcard Selection

```sql
SELECT *
```

### Field Aliases

```sql
SELECT sub AS subject, ses AS session, filepath AS file_path
```

### Aggregate Functions

```sql
SELECT COUNT(*) AS total_files
SELECT sub, COUNT(*) AS files_per_subject
SELECT AVG(metadata.RepetitionTime) AS mean_tr
SELECT MAX(run) AS max_run, MIN(run) AS min_run
```

**Available Functions:**
- `COUNT(*)` - Count rows
- `COUNT(field)` - Count non-null values
- `AVG(field)` - Average of numeric values
- `MAX(field)` - Maximum value
- `MIN(field)` - Minimum value
- `SUM(field)` - Sum of numeric values
- `ARRAY_AGG(field)` - Collect values into array
- `ARRAY_AGG(field WHERE condition)` - Collect filtered values into array

### Auto-Aggregation with GROUP BY

When using GROUP BY, non-grouped fields are automatically aggregated into arrays:

```sql
-- Without GROUP BY: Returns individual files
SELECT sub, filename

-- With GROUP BY: Returns arrays of filenames per subject
SELECT sub, filename GROUP BY sub
```

**Result:**
```json
[
  {
    "sub": "01",
    "filename": ["sub-01_T1w.nii", "sub-01_task-rest_bold.nii", ...]
  }
]
```

## WHERE Clause

The WHERE clause filters results based on conditions.

### Basic Comparisons

```sql
-- Equality
sub=01
task=rest
datatype=func

-- Inequality
run!=1
metadata.RepetitionTime>2.0
participants.age<30
```

### Logical Operators

```sql
-- AND
sub=01 AND task=rest

-- OR
task=rest OR task=nback

-- NOT
NOT datatype=func

-- Grouping with parentheses
(sub=01 OR sub=02) AND datatype=func
```

### Pattern Matching

#### Wildcard Patterns
```sql
-- Asterisk (*) matches any characters
suffix=*bold*
filename=sub-01*

-- Question mark (?) matches single character
suffix=T?w
```

#### Regular Expressions
```sql
-- Regex matching with ~= operator
sub~="0[1-5]"
task~=".*back.*"
filename~="sub-\d+_ses-\d+.*"
```

#### SQL-style LIKE
```sql
-- LIKE with % and _ wildcards
task LIKE %back%
filename LIKE sub-01_%
```

### Range Queries

```sql
-- Numeric ranges
run=[1:3]          -- run 1, 2, or 3
metadata.EchoTime=[0.01:0.05]

-- List membership
sub IN [01, 02, 03]
task IN [rest, nback, faces]
```

### Null and Existence Checks

```sql
-- Check if field exists
task
metadata.RepetitionTime

-- Check for specific values including null
run=null
metadata.EchoTime!=null
```

## GROUP BY and Aggregation

GROUP BY groups results by specified fields and enables aggregation.

### Basic Grouping

```sql
SELECT sub, COUNT(*) GROUP BY sub
```

### Multiple Fields

```sql
SELECT sub, ses, task, COUNT(*)
GROUP BY sub, ses, task
```

### Auto-Aggregation Behavior

Fields not in GROUP BY are automatically aggregated into arrays or single values:

```sql
SELECT sub, filename, COUNT(*) GROUP BY sub
```

**Result shows arrays of filenames per subject:**
```json
[
  {
    "sub": "01",
    "filename": ["file1.nii", "file2.nii"],
    "count": 2
  }
]
```

**Auto-Aggregation Logic:**
- **Single unique value** → returned as string/number (not array)
- **Multiple unique values** → returned as array
- **No values** → null
- **Mixed null/non-null** → array contains only non-null values

{: .highlight }
> **Critical for Reconstruction Workflows:** GROUP BY creates filename arrays

```sql
-- QSM magnitude/phase grouping
SELECT sub, ses, acq, filename, COUNT(*) as files
WHERE (part=mag OR part=phase) AND suffix=MEGRE
GROUP BY sub, ses, acq
```

**Result includes filename arrays for each reconstruction group:**
```json
[
  {
    "sub": "01",
    "ses": "1",
    "acq": "GRE",
    "filename": [
      "sub-01_ses-1_acq-GRE_part-mag_MEGRE.nii",
      "sub-01_ses-1_acq-GRE_part-phase_MEGRE.nii"
    ],
    "files": 2
  }
]
```

## HAVING Clause

HAVING filters grouped results based on aggregate conditions.

```sql
-- Subjects with more than 10 files
SELECT sub, COUNT(*)
GROUP BY sub
HAVING COUNT(*) > 10

-- Tasks with sufficient data
SELECT task, COUNT(*)
GROUP BY task
HAVING COUNT(*) >= 20
```

**Supported Operators in HAVING:**
- `>`, `<`, `>=`, `<=`, `=`, `!=`

## ORDER BY Clause

ORDER BY sorts results by specified fields.

### Basic Sorting

```sql
ORDER BY sub
ORDER BY sub ASC          -- Ascending (default)
ORDER BY sub DESC         -- Descending
```

### Multiple Fields

```sql
ORDER BY sub ASC, ses DESC, run ASC
```

### Sorting with Aggregation

```sql
SELECT task, COUNT(*)
GROUP BY task
ORDER BY COUNT(*) DESC    -- Most common tasks first
```

## DISTINCT

DISTINCT removes duplicate rows from results.

### Basic Usage

```sql
SELECT DISTINCT sub           -- Unique subjects
SELECT DISTINCT task          -- Unique tasks
SELECT DISTINCT datatype      -- Unique datatypes
```

### Multiple Fields

```sql
SELECT DISTINCT sub, ses      -- Unique subject/session combinations
```

### With WHERE Conditions

```sql
SELECT DISTINCT task WHERE datatype=func
```

## Operators

### Comparison Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `=` | Equal | `sub=01` |
| `!=` | Not equal | `run!=1` |
| `>` | Greater than | `run>1` |
| `<` | Less than | `participants.age<30` |
| `>=` | Greater or equal | `metadata.RepetitionTime>=2.0` |
| `<=` | Less or equal | `run<=3` |

### Pattern Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `~=` | Regex match | `sub~="0[1-3]"` |
| `LIKE` | SQL-style pattern | `task LIKE %back%` |

### Logical Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `AND` | Logical AND | `sub=01 AND task=rest` |
| `OR` | Logical OR | `task=rest OR task=nback` |
| `NOT` | Logical NOT | `NOT datatype=func` |

### Set Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `IN` | List membership | `sub IN [01, 02, 03]` |
| `[start:end]` | Range | `run=[1:3]` |

## Data Types

### Automatic Type Detection

BIQL automatically detects and converts data types:

```sql
-- String comparison
sub="01"

-- Numeric comparison
run=1
metadata.RepetitionTime=2.0

-- Boolean (for metadata)
metadata.SliceEncodingDirection=true
```

### Type Coercion

- Strings that look like numbers are converted for comparison
- `"01"` and `1` are treated as equivalent for numeric operations
- String comparison used as fallback when numeric conversion fails

## BIDS Entities

BIQL provides direct access to all BIDS entities:

### Standard Entities

```sql
sub              -- Subject ID
ses              -- Session ID
task             -- Task name
run              -- Run number
acq              -- Acquisition parameters
rec              -- Reconstruction algorithm
space            -- Template space
res              -- Resolution
den              -- Density
desc             -- Description
```

### Modality-Specific Entities

```sql
-- fMRI
echo             -- Echo number
flip             -- Flip angle
inv              -- Inversion time
mt               -- Magnetization transfer
part             -- Part (mag, phase, real, imag)
recording        -- Recording type

-- DWI
dir              -- Diffusion direction
dwi              -- DWI identifier

-- Anatomical
acq              -- Acquisition
ce               -- Contrast enhancement
rec              -- Reconstruction
mod              -- Modality
```

### Derivatives Entities

```sql
-- Processing pipeline
pipeline         -- Pipeline name
atlas            -- Atlas used
roi              -- Region of interest
model            -- Statistical model
```

### File Properties

```sql
datatype         -- BIDS datatype (anat, func, dwi, etc.)
suffix           -- File suffix (T1w, bold, dwi, etc.)
extension        -- File extension (.nii, .json, .tsv)
filename         -- Complete filename
filepath         -- Full file path
relative_path    -- Path relative to BIDS root
```

## Metadata Access

Access JSON metadata using dot notation:

### Basic Metadata Access

```sql
metadata.RepetitionTime
metadata.EchoTime
metadata.FlipAngle
metadata.MagneticFieldStrength
```

### Nested Metadata

```sql
metadata.SliceEncodingDirection
metadata.PhaseEncodingDirection
metadata.TaskName
metadata.Instructions
```

### Metadata Queries

```sql
-- Find scans with specific parameters
WHERE metadata.RepetitionTime=2.0
WHERE metadata.EchoTime<0.05
WHERE metadata.MagneticFieldStrength=3.0

-- Group by acquisition parameters
SELECT metadata.RepetitionTime, COUNT(*)
GROUP BY metadata.RepetitionTime
```

### Metadata Inheritance

BIQL follows BIDS inheritance rules:
- Dataset-level metadata applies to all files
- Subject/session-level metadata overrides dataset-level
- File-specific metadata has highest priority

## Participant Data

Access participant information from `participants.tsv`:

### Basic Participant Access

```sql
participants.age
participants.sex
participants.group
participants.handedness
```

### Participant Queries

```sql
-- Filter by demographics
WHERE participants.age>25
WHERE participants.sex="F"
WHERE participants.group="control"

-- Group by participant characteristics
SELECT participants.group, COUNT(*)
GROUP BY participants.group
```

### Combined Entity and Participant Queries

```sql
-- Functional scans from female participants over 25
SELECT sub, task, participants.age, participants.sex
WHERE datatype=func AND participants.sex="F" AND participants.age>25
```

## Query Examples by Use Case

### Dataset Exploration

```sql
-- Overview of available data
SELECT datatype, COUNT(*) GROUP BY datatype

-- Subjects and sessions
SELECT DISTINCT sub, ses ORDER BY sub, ses

-- Available tasks
SELECT DISTINCT task WHERE datatype=func
```

### Quality Control

```sql
-- Check data completeness
SELECT sub, COUNT(*) as total_files
GROUP BY sub
ORDER BY total_files

-- Find missing sessions
SELECT sub, ses, COUNT(*)
GROUP BY sub, ses
HAVING COUNT(*) < 10
```

### Processing Pipelines

```sql
-- T1w files for preprocessing
SELECT sub, ses, filepath WHERE suffix=T1w

-- Functional runs for specific task
SELECT sub, ses, run, filepath
WHERE datatype=func AND task=nback
ORDER BY sub, ses, run
```

### QSM Workflows

```sql
-- QSM reconstruction groups
SELECT sub, ses, acq, filename, COUNT(*)
WHERE (part=mag OR part=phase) AND suffix=MEGRE
GROUP BY sub, ses, acq

-- Separate magnitude and phase files for QSM
SELECT sub, ses, acq, run,
       ARRAY_AGG(filename WHERE part='mag') AS mag_filenames,
       ARRAY_AGG(filename WHERE part='phase') AS phase_filenames
WHERE (part='mag' OR part='phase') AND suffix=MEGRE
GROUP BY sub, ses, acq, run

-- Multi-echo parameters
SELECT DISTINCT echo, metadata.EchoTime
WHERE suffix=MEGRE
ORDER BY metadata.EchoTime
```

## Performance Tips

1. **Use DISTINCT for exploration** - Faster than GROUP BY for unique values
2. **Filter early** - Put selective conditions first in WHERE clause
3. **Limit field selection** - Only SELECT fields you need
4. **Index-friendly queries** - Entity-based filters are fastest
5. **Avoid complex regex** - Use wildcards when possible

## Error Handling

BIQL gracefully handles common issues without crashing:

### Graceful Failure Modes

- **Missing fields** → Return null or exclude from results
- **Type mismatches** → Fall back to string comparison
- **Invalid regex** → Skip pattern matching, continue query
- **Missing metadata** → Return null values
- **Malformed queries** → Clear error messages with position

### Type Conversion Fallbacks

```sql
-- Numeric comparison attempts first, falls back to string
WHERE sub>5  -- Works even when sub is "01" (string comparison)
WHERE run<10 -- Converts "3" to 3 for numeric comparison
```

### Missing Field Handling

```sql
-- Queries against non-existent fields return empty results
WHERE nonexistent_field=value  -- Returns no results, no error

-- Missing metadata is handled gracefully
WHERE metadata.MissingParameter>1.0  -- Returns no results
```

### Null Value Aggregation

```sql
-- Mixed null/non-null values in GROUP BY
SELECT sub, metadata.RepetitionTime GROUP BY sub
-- Result: Only non-null TR values included in arrays
```

Continue to [CLI Reference](cli.html) for command-line usage details.
