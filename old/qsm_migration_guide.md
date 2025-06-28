# QSMxT BIDS Parser → BIQL Migration Guide

This guide shows how to replace your custom BIDS parser with equivalent BIQL queries for QSM processing.

## Key QSM Entities in BIDS

Your original parser focused on these entities for QSM reconstruction groups:

- **`part`**: `mag` (magnitude) or `phase` 
- **`echo`**: Echo number for multi-echo sequences (1, 2, 3, ...)
- **`acq`**: Acquisition parameters (`mygrea`, `mygreb`, etc.)
- **`suffix`**: `T2starw` (single echo) or `MEGRE` (multi-echo)
- **Standard BIDS**: `sub`, `ses`, `run`

## Migration Examples

### 1. Basic QSM File Discovery

**Original Parser Goal**: Find all magnitude and phase files for QSM processing

**BIQL Query**:
```sql
-- Find all QSM-relevant files
part=mag OR part=phase

-- More specific: only QSM sequences
(part=mag OR part=phase) AND (suffix=T2starw OR suffix=MEGRE)
```

### 2. QSM Reconstruction Groups

**Original Parser Goal**: Group files by `(subject, session, acquisition, run)` for reconstruction

**BIQL Query**:
```sql
-- Group QSM files by reconstruction units
SELECT sub, ses, acq, run, COUNT(*) 
WHERE (part=mag OR part=phase) AND (suffix=T2starw OR suffix=MEGRE)
GROUP BY sub, ses, acq, run
```

### 3. Single-Echo T2* Acquisitions

**Original Parser Pattern**: Files matching `*_part-{mag|phase}_T2starw.*`

**BIQL Query**:
```sql
-- Find T2* single-echo files
suffix=T2starw AND (part=mag OR part=phase)

-- Get magnitude files only
suffix=T2starw AND part=mag

-- With file details
SELECT sub, ses, part, filename WHERE suffix=T2starw
```

### 4. Multi-Echo MEGRE Acquisitions

**Original Parser Pattern**: Files matching `*_echo-{N}_part-{mag|phase}_MEGRE.*`

**BIQL Query**:
```sql
-- Find multi-echo MEGRE files
suffix=MEGRE AND (part=mag OR part=phase)

-- Group by echo number
SELECT echo, COUNT(*) WHERE suffix=MEGRE GROUP BY echo

-- Get complete echo series for a subject
SELECT sub, echo, part, filename 
WHERE sub=2 AND suffix=MEGRE 
ORDER BY echo, part
```

### 5. Specific Acquisition Parameters

**Original Parser Pattern**: Files with specific acquisition names

**BIQL Query**:
```sql
-- Find specific acquisition
acq=mygrea AND suffix=MEGRE

-- Multiple acquisitions
acq=mygrea OR acq=mygreb

-- Pattern matching acquisitions
acq~=/myg.*/

-- Complex: multi-echo with specific acquisition
SELECT sub, acq, echo, part, filename 
WHERE suffix=MEGRE AND acq~=/myg.*/ 
ORDER BY sub, acq, echo, part
```

### 6. Session-Specific Queries

**Original Parser Goal**: Handle multiple sessions per subject

**BIQL Query**:
```sql
-- Files from specific session
ses=20231020

-- All sessions for a subject
sub=4 AND ses~=/.*/

-- Compare sessions
SELECT ses, COUNT(*) WHERE sub=4 GROUP BY ses
```

### 7. Complete Magnitude-Phase Pairs

**Original Parser Goal**: Ensure both magnitude and phase files exist for reconstruction

**BIQL Strategy**: Two-step process
```sql
-- Step 1: Find all magnitude files
part=mag AND suffix=MEGRE

-- Step 2: For each mag file, verify corresponding phase exists
-- (This requires programmatic logic - see examples/qsm_examples.py)
```

### 8. Derivatives and Masks

**Original Parser Goal**: Find masks in derivatives directories

**BIQL Query**:
```sql
-- Find masks
suffix=mask

-- Masks for specific subject
suffix=mask AND sub=1

-- All derivatives
SELECT * WHERE relative_path~=/derivatives/
```

### 9. Quality Control Queries

**BIQL Queries for QC**:
```sql
-- Check for incomplete groups (missing phase files)
SELECT sub, ses, acq, run, part, COUNT(*) 
WHERE suffix=T2starw 
GROUP BY sub, ses, acq, run, part

-- Find orphaned files (no matching mag/phase pair)
part=mag AND NOT EXISTS (corresponding phase file)

-- Verify echo counts match
SELECT sub, ses, acq, run, echo, COUNT(*) 
WHERE suffix=MEGRE 
GROUP BY sub, ses, acq, run, echo
```

### 10. Advanced Reconstruction Planning

**BIQL Queries for processing pipeline**:
```sql
-- Get processing order by field strength
SELECT sub, metadata.MagneticFieldStrength, COUNT(*) 
WHERE part=mag 
GROUP BY sub, metadata.MagneticFieldStrength 
ORDER BY metadata.MagneticFieldStrength

-- Find multi-run acquisitions needing combination
SELECT sub, ses, acq, COUNT(*) 
WHERE run~=/.*/ 
GROUP BY sub, ses, acq 
HAVING COUNT(*) > 1

-- Echo time analysis
SELECT echo, metadata.EchoTime, COUNT(*) 
WHERE suffix=MEGRE AND part=mag 
GROUP BY echo, metadata.EchoTime 
ORDER BY metadata.EchoTime
```

## Key BIQL Advantages Over Custom Parser

1. **Standardized**: Uses SQL-like syntax everyone understands
2. **Flexible**: Easy to modify queries without changing code
3. **Powerful**: Supports complex conditions, pattern matching, aggregation
4. **Maintainable**: No need to maintain custom parsing logic
5. **Extensible**: Easy to add new query types as needs evolve

## Migration Strategy

1. **Replace parser calls** with BIQL queries
2. **Use GROUP BY** to replicate your grouping logic
3. **Leverage pattern matching** for flexible file selection
4. **Add validation queries** for quality control
5. **Integrate with QSMxT pipeline** using the Python API

## Example Integration

```python
from biql import BIDSDataset, BIQLEvaluator, BIQLParser

# Replace your parse_bids_directory() function
def get_qsm_groups(bids_dir):
    dataset = BIDSDataset(bids_dir)
    evaluator = BIQLEvaluator(dataset)
    
    # Get QSM reconstruction groups
    parser = BIQLParser.from_string(
        "SELECT sub, ses, acq, run, COUNT(*) "
        "WHERE (part=mag OR part=phase) AND (suffix=T2starw OR suffix=MEGRE) "
        "GROUP BY sub, ses, acq, run"
    )
    query = parser.parse()
    return evaluator.evaluate(query)
```

This approach gives you all the functionality of your original parser with much more flexibility and power!