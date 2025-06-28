---
layout: default
title: Examples
nav_order: 5
description: "Real-world BQL query patterns and cookbook recipes"
---

# Query Examples

Real-world BQL query patterns and cookbook recipes for common neuroimaging workflows.

## Dataset Exploration

### Quick Dataset Overview

```sql
-- Get basic dataset statistics
SELECT datatype, COUNT(*) 
GROUP BY datatype
```

```sql
-- See all available subjects and sessions
SELECT DISTINCT sub, ses 
ORDER BY sub, ses
```

```sql
-- Find all unique tasks
SELECT DISTINCT task 
WHERE datatype=func
```

### Entity Discovery

```sql
-- What acquisitions are available?
SELECT DISTINCT acq 
WHERE acq

-- What echo times are used?
SELECT DISTINCT metadata.EchoTime 
WHERE metadata.EchoTime 
ORDER BY metadata.EchoTime
```

### Data Completeness Check

```sql
-- Files per subject
SELECT sub, COUNT(*) as total_files 
GROUP BY sub 
ORDER BY total_files DESC
```

```sql
-- Session completeness
SELECT sub, ses, task, COUNT(*) as runs
WHERE datatype=func
GROUP BY sub, ses, task
ORDER BY sub, ses, task
```

## File Discovery

### Basic File Lists

```sql
-- All T1w anatomical scans
SELECT sub, ses, filepath 
WHERE suffix=T1w
ORDER BY sub, ses
```

```sql
-- Functional scans for specific task
SELECT sub, ses, run, filepath 
WHERE datatype=func AND task=nback
ORDER BY sub, ses, run
```

### Pattern Matching

```sql
-- Find all BOLD variants
SELECT suffix, COUNT(*) 
WHERE suffix=*bold*
GROUP BY suffix
```

```sql
-- Multi-echo sequences
SELECT sub, ses, echo, filepath
WHERE echo AND datatype=func
ORDER BY sub, ses, echo
```

### Complex Filtering

```sql
-- High-resolution structural scans
SELECT sub, filepath, metadata.VoxelSize
WHERE suffix=T1w AND metadata.VoxelSize<[0.5:1.0]
```

```sql
-- Fast acquisition functional scans
SELECT sub, task, metadata.RepetitionTime, filepath
WHERE datatype=func AND metadata.RepetitionTime<2.0
ORDER BY metadata.RepetitionTime
```

## Quality Control

### Missing Data Detection

```sql
-- Subjects missing resting-state data
SELECT DISTINCT sub 
WHERE sub NOT IN (
  SELECT DISTINCT sub WHERE task=rest
)
```

```sql
-- Sessions with incomplete task coverage
SELECT sub, ses, COUNT(DISTINCT task) as unique_tasks
WHERE datatype=func
GROUP BY sub, ses
HAVING COUNT(DISTINCT task) < 3
```

### Outlier Detection

```sql
-- Unusually short/long scans
SELECT sub, ses, task, run, metadata.RepetitionTime, filepath
WHERE datatype=func AND (
  metadata.RepetitionTime < 1.0 OR 
  metadata.RepetitionTime > 4.0
)
```

```sql
-- Files with unusual sizes (proxy check)
SELECT sub, filepath, filename
WHERE filename=*_bold.nii* AND 
      filepath~=".*([5-9][0-9]{7,}|[1-9][0-9]{8,}).*"
```

### Consistency Checks

```sql
-- Check for consistent task parameters
SELECT task, metadata.RepetitionTime, COUNT(*) as count
WHERE datatype=func
GROUP BY task, metadata.RepetitionTime
ORDER BY task, metadata.RepetitionTime
```

```sql
-- Find sessions with mixed acquisition parameters
SELECT sub, ses, acq, COUNT(*) as files
WHERE datatype=func
GROUP BY sub, ses, acq
HAVING COUNT(DISTINCT metadata.RepetitionTime) > 1
```

## Processing Workflows

### fMRI Preprocessing

```sql
-- Generate T1w-BOLD pairs for registration
SELECT 
  sub, ses,
  t1.filepath as t1w_file,
  bold.filepath as bold_file
FROM 
  (SELECT sub, ses, filepath WHERE suffix=T1w) t1,
  (SELECT sub, ses, filepath WHERE datatype=func) bold
WHERE t1.sub = bold.sub AND t1.ses = bold.ses
```

```sql
-- Find fieldmap pairs for distortion correction
SELECT sub, ses, dir, filename
WHERE suffix=epi AND (dir=AP OR dir=PA)
ORDER BY sub, ses, dir
```

### Group Analysis Setup

```sql
-- Control vs patient groups
SELECT participants.group, COUNT(*) as n_subjects
WHERE participants.group IN [control, patient]
GROUP BY participants.group
```

```sql
-- Age-matched cohorts
SELECT 
  participants.group,
  AVG(participants.age) as mean_age,
  COUNT(*) as n_subjects
WHERE participants.age>[18:65]
GROUP BY participants.group
```

### Multi-session Studies

```sql
-- Longitudinal data completeness
SELECT sub, COUNT(DISTINCT ses) as sessions, ses
WHERE datatype=func AND task=rest
GROUP BY sub
HAVING COUNT(DISTINCT ses) >= 2
ORDER BY sessions DESC
```

```sql
-- Change in acquisition parameters over time
SELECT ses, metadata.RepetitionTime, COUNT(*) as scans
WHERE task=rest
GROUP BY ses, metadata.RepetitionTime
ORDER BY ses
```

## Advanced Queries

### Metadata Analysis

```sql
-- Scanner-specific analysis
SELECT 
  metadata.Manufacturer,
  metadata.MagneticFieldStrength,
  COUNT(*) as scans
WHERE datatype=func
GROUP BY metadata.Manufacturer, metadata.MagneticFieldStrength
```

```sql
-- Acquisition time analysis
SELECT 
  sub, 
  metadata.AcquisitionTime,
  COUNT(*) as scans
WHERE metadata.AcquisitionTime
GROUP BY sub, metadata.AcquisitionTime
ORDER BY metadata.AcquisitionTime
```

### Complex Aggregations

```sql
-- Average scan parameters by site
SELECT 
  participants.site,
  AVG(metadata.RepetitionTime) as mean_tr,
  AVG(metadata.EchoTime) as mean_te,
  COUNT(*) as total_scans
WHERE datatype=func
GROUP BY participants.site
ORDER BY participants.site
```

```sql
-- Task duration estimates
SELECT 
  task,
  AVG(metadata.RepetitionTime * metadata.NumberOfVolumes) as duration_sec,
  COUNT(*) as n_runs
WHERE datatype=func AND metadata.NumberOfVolumes
GROUP BY task
ORDER BY duration_sec DESC
```

## Specialized Workflows

### QSM (Quantitative Susceptibility Mapping)

```sql
-- QSM reconstruction groups with filename arrays
SELECT 
  sub, ses, acq, run,
  filename,
  COUNT(*) as files_in_group
WHERE (part=mag OR part=phase) AND suffix=MEGRE
GROUP BY sub, ses, acq, run
HAVING COUNT(*) >= 2
ORDER BY sub, ses, acq, run
```

{: .important }
> **Critical**: The `filename` field becomes an array containing all files for reconstruction:

```json
[
  {
    "sub": "01",
    "ses": "1", 
    "acq": "GRE",
    "filename": [
      "sub-01_ses-1_acq-GRE_part-mag_echo-1_MEGRE.nii",
      "sub-01_ses-1_acq-GRE_part-phase_echo-1_MEGRE.nii",
      "sub-01_ses-1_acq-GRE_part-mag_echo-2_MEGRE.nii",
      "sub-01_ses-1_acq-GRE_part-phase_echo-2_MEGRE.nii"
    ],
    "files_in_group": 4
  }
]
```

```sql
-- Multi-echo parameter validation
SELECT 
  sub, ses, echo, part,
  metadata.EchoTime,
  filename
WHERE suffix=MEGRE AND echo=[1:5]
ORDER BY sub, ses, echo, part
```

```sql
-- Find complete magnitude/phase pairs
SELECT 
  sub, ses, echo,
  COUNT(DISTINCT part) as parts,
  filename
WHERE suffix=MEGRE AND part IN [mag, phase]
GROUP BY sub, ses, echo
HAVING COUNT(DISTINCT part) = 2
ORDER BY sub, ses, echo
```

```sql
-- Discover unique echo times for parameter validation
SELECT DISTINCT metadata.EchoTime
WHERE suffix=MEGRE AND metadata.EchoTime
ORDER BY metadata.EchoTime
```

### DTI/DWI Processing

```sql
-- DWI sequences with b-values
SELECT 
  sub, ses, run,
  metadata.BValue,
  filepath
WHERE datatype=dwi
ORDER BY sub, ses, metadata.BValue, run
```

```sql
-- Multi-shell DWI validation
SELECT 
  sub, ses,
  COUNT(DISTINCT metadata.BValue) as shells,
  metadata.BValue
WHERE datatype=dwi
GROUP BY sub, ses
HAVING COUNT(DISTINCT metadata.BValue) > 1
ORDER BY shells DESC
```

### ASL (Arterial Spin Labeling)

```sql
-- ASL control/label pairs
SELECT 
  sub, ses, asl,
  COUNT(*) as volumes,
  filepath
WHERE suffix=asl
GROUP BY sub, ses, asl
ORDER BY sub, ses
```

### Resting-State Networks

```sql
-- Long resting-state sessions
SELECT 
  sub, ses, run,
  metadata.RepetitionTime * metadata.NumberOfVolumes as duration_sec,
  filepath
WHERE task=rest AND datatype=func
HAVING duration_sec > 600
ORDER BY duration_sec DESC
```

## Export and Integration

### File List Generation

```bash
# Export functional files for FSL
biql "datatype=func AND task=nback" --format paths > nback_files.txt

# Create processing manifest
biql "SELECT sub, ses, run, filepath WHERE suffix=T1w" \
     --format csv > t1w_manifest.csv
```

### Pipeline Integration

```sql
-- BIDS Apps participant list
SELECT DISTINCT sub
WHERE datatype=func AND task IN [rest, nback]
```

```sql
-- fMRIPrep input validation
SELECT sub, COUNT(DISTINCT suffix) as modalities
WHERE suffix IN [T1w, bold] 
GROUP BY sub
HAVING COUNT(DISTINCT suffix) = 2
```

### Custom Processing Scripts

```python
import subprocess
import json

# Get functional files via BQL
result = subprocess.run([
    'biql', 
    'SELECT sub, ses, task, run, filepath WHERE datatype=func',
    '--format', 'json'
], capture_output=True, text=True)

files = json.loads(result.stdout)
for file_info in files:
    process_func_file(file_info['filepath'])
```

## Performance Optimization

### Efficient Queries

```sql
-- Fast: Use DISTINCT for exploration
SELECT DISTINCT task WHERE datatype=func

-- Slower: GROUP BY when you only need unique values
SELECT task, COUNT(*) WHERE datatype=func GROUP BY task
```

```sql
-- Fast: Filter early in WHERE clause
SELECT filepath WHERE sub=01 AND datatype=func AND task=rest

-- Slower: Complex conditions without entity filters
SELECT filepath WHERE metadata.RepetitionTime>2.0 AND task=rest
```

### Large Dataset Strategies

```sql
-- Batch processing by subject
SELECT sub, filepath 
WHERE sub=01 AND datatype=func

-- Instead of processing all subjects at once
SELECT sub, filepath 
WHERE datatype=func
```

## Troubleshooting Queries

### Debug Empty Results

```sql
-- Check what data is available
SELECT DISTINCT datatype

-- Verify entity values
SELECT DISTINCT task WHERE datatype=func

-- Test simplified query
SELECT COUNT(*) WHERE datatype=func
```

### Validate Assumptions

```sql
-- Check metadata availability
SELECT COUNT(*) as with_metadata
WHERE metadata.RepetitionTime

-- Verify participants data
SELECT COUNT(*) as with_demographics  
WHERE participants.age
```

### Common Gotchas

```sql
-- String vs numeric comparison
WHERE run="1"    -- String comparison
WHERE run=1      -- Numeric comparison

-- Wildcard patterns need quotes
WHERE task=n*back    -- Error: invalid syntax
WHERE task="n*back"  -- Correct wildcard pattern

-- Metadata access requires dot notation
WHERE RepetitionTime>2.0     -- Error: field not found
WHERE metadata.RepetitionTime>2.0  -- Correct
```

## Recipe Collection

### Quick Dataset Summary

```bash
#!/bin/bash
echo "=== Dataset Overview ==="
biql "SELECT datatype, COUNT(*) GROUP BY datatype" --format table

echo -e "\n=== Subject Count ==="
biql "SELECT COUNT(DISTINCT sub)" --format table

echo -e "\n=== Available Tasks ==="
biql "SELECT DISTINCT task WHERE datatype=func" --format table
```

### Quality Control Report

```sql
-- Run each query and review results

-- 1. Data completeness by subject
SELECT sub, ses, COUNT(*) as files
GROUP BY sub, ses
ORDER BY files

-- 2. Missing anatomical scans
SELECT sub 
WHERE sub NOT IN (SELECT DISTINCT sub WHERE suffix=T1w)

-- 3. Inconsistent task parameters
SELECT task, metadata.RepetitionTime, COUNT(*)
WHERE datatype=func
GROUP BY task, metadata.RepetitionTime
ORDER BY task
```

### Processing Pipeline Setup

```bash
#!/bin/bash
# Generate file lists for multi-step pipeline

echo "Generating T1w file list..."
biql "suffix=T1w" --format paths > t1w_files.txt

echo "Generating functional file list..."
biql "datatype=func" --format csv > func_manifest.csv

echo "Creating subject list..."
biql "SELECT DISTINCT sub" --format json > subjects.json

echo "Pipeline input files ready!"
```

Ready to start querying? Check out the [Quickstart Guide](quickstart.html) or dive into the [Language Reference](language.html) for complete syntax details.