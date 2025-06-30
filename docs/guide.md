---
title: BIQL Tutorial
nav_order: 3
---

# BIQL Tutorial

This tutorial demonstrates how to use the BIDS Query Language (BIQL) to query neuroimaging datasets.
The examples below are automatically executed and updated whenever the documentation is built.


Welcome to the BIQL (BIDS Query Language) tutorial! This guide will walk you through
using BIQL to query BIDS neuroimaging datasets. We'll start with basic queries and
progressively explore more advanced features.

## What is BIQL?

BIQL is a SQL-like query language designed specifically for querying Brain Imaging
Data Structure (BIDS) datasets. It allows you to:

- Search for specific files based on BIDS entities (subject, session, task, etc.)
- Filter data using metadata from JSON sidecars
- Access participant information from participants.tsv
- Perform aggregations and grouping operations
- Export results in various formats

## Prerequisites

First, let's set up our environment and get the example data:


```python
import tempfile
from pathlib import Path
from biql import create_query_engine

# Set up paths - use a temporary directory that works in different environments
bids_examples_dir = Path(tempfile.gettempdir()) / "bids-examples"

# Clone bids-examples if it doesn't exist
if not bids_examples_dir.exists():
    !git clone https://github.com/bids-standard/bids-examples.git {bids_examples_dir}
else:
    print(f"✅ bids-examples already exists at {bids_examples_dir}")
```

## Part 1: Basic Queries

Let's start with the synthetic dataset from bids-examples. This is a simple dataset
that's perfect for learning BIQL basics.


```python
dataset_path = bids_examples_dir / "synthetic"
q = create_query_engine(dataset_path)

q.dataset_stats()
```

### Simple Entity Queries

The most basic BIQL queries filter files by BIDS entities. You can query by any
BIDS entity that appears in your filenames:


```python
q.run_query("sub=01", format="dataframe").head(5)
```


```python
results = q.run_query("datatype=func")
len(results)  # Number of functional files
```


```python
q.run_query("SELECT DISTINCT task WHERE datatype=func", format="dataframe")
```

### Combining Conditions

You can combine multiple conditions using AND, OR, and NOT operators:


```python
q.run_query("datatype=anat AND suffix=T1w", format="dataframe").head(5)
```


```python
q.run_query("task=nback OR task=rest", format="dataframe")
```

### Using WHERE Clause

For more SQL-like queries, you can use the WHERE clause:


```python
q.run_query("WHERE sub=01 AND datatype=func", format="dataframe")
```

## Part 2: SELECT Clause and Field Selection

By default, BIQL returns all available fields. Use SELECT to choose specific fields:


```python
q.run_query(
    "SELECT sub, task, run, filename WHERE datatype=func",
    format="dataframe"
)
```


```python
q.run_query(
    "SELECT sub, relative_path WHERE suffix=T1w",
    format="dataframe"
)
```

## Part 3: Pattern Matching

BIQL supports wildcards and regular expressions for flexible matching:


```python
results = q.run_query("suffix=*bold*")
len(results)  # Count of files with 'bold' in suffix
```


```python
q.run_query(
    "SELECT DISTINCT task WHERE task~=\".*back.*\"",
    format="dataframe"
)
```

## Part 4: Ranges and Lists

BIQL supports range queries and IN operators for matching multiple values:


```python
q.run_query(
    "SELECT sub, ARRAY_AGG(DISTINCT task) as tasks, COUNT(*) as total_files "
    "WHERE sub IN ['01', '02', '03'] "
    "GROUP BY sub",
    format="json"
)
```


```python
q.run_query(
    "SELECT task, run, COUNT(*) as file_count, "
    "COUNT(DISTINCT sub) as subjects "
    "WHERE datatype=func "
    "GROUP BY task, run "
    "ORDER BY task, run",
    format="dataframe"
)
```

## Part 5: Grouping and Aggregation

BIQL supports SQL-like grouping and aggregation functions:


```python
q.run_query("SELECT sub, COUNT(*) GROUP BY sub", format="dataframe")
```


```python
q.run_query(
    "SELECT sub, datatype, COUNT(*) GROUP BY sub, datatype",
    format="json"
)
```

## Part 6: Working with Metadata

BIQL can query JSON sidecar metadata using the `metadata.` namespace.
The synthetic dataset has task-level metadata files like `task-nback_bold.json`:


```python
q.run_query(
    "SELECT task, COUNT(*) as file_count, "
    "ARRAY_AGG(DISTINCT sub) as subjects_with_task, "
    "ARRAY_AGG(DISTINCT datatype) as datatypes "
    "GROUP BY task",
    format="json"
)
```


```python
q.run_query(
    "SELECT datatype, COUNT(*) as total_files, "
    "COUNT(DISTINCT sub) as subjects, "
    "ARRAY_AGG(DISTINCT sub) as subject_list "
    "GROUP BY datatype "
    "ORDER BY total_files DESC",
    format="json"
)
```

## Part 7: Participant Information

Access participant demographics using the `participants.` namespace:


```python
q.run_query(
    "SELECT DISTINCT sub, participants.age, participants.sex",
    format="dataframe"
)
```


```python
q.run_query(
    "SELECT sub, task, participants.age WHERE participants.age > 25",
    format="dataframe"
)
```

## Part 8: Advanced Queries

Let's combine multiple features for more complex queries:


```python
q.run_query("""
    SELECT sub, ses, task, COUNT(*) as n_runs
    WHERE datatype=func AND task != rest
    GROUP BY sub, ses, task
    HAVING COUNT(*) > 1
    ORDER BY sub, task
""", format="json")
```


```python
q.run_query("""
    SELECT sub, task,
           ARRAY_AGG(filename WHERE suffix='bold') as imaging_files,
           ARRAY_AGG(filename WHERE run='01') as run01_files,
           ARRAY_AGG(filename WHERE run='02') as run02_files
    WHERE datatype=func
    GROUP BY sub, task
""", format="table")  # Using table format since arrays don't display well in dataframes
```

## Part 9: Output Formats

BIQL supports multiple output formats for different use cases:


```python
sample_query = "SELECT sub, task, run WHERE datatype=func AND sub=01"

print(q.run_query(sample_query, format="table"))
```


```python
print(q.run_query(sample_query, format="csv"))
```


```python
results_json = q.run_query(sample_query, format="json")
results_json[:2]  # Show first 2 entries
```


```python
print(q.run_query("WHERE sub=01 AND suffix=T1w", format="paths"))
```


```python
q.run_query(sample_query, format="dataframe")
```

## Part 10: Real-World Examples

Let's look at some practical queries you might use in neuroimaging research:


```python
q.run_query("""
    SELECT sub,
           COUNT(*) as total_files,
           COUNT(DISTINCT datatype) as datatypes,
           ARRAY_AGG(DISTINCT datatype) as available_data
    GROUP BY sub
""", format="json")
```


```python
q.run_query("""
    SELECT sub, ses,
           COUNT(*) as files_per_session,
           ARRAY_AGG(DISTINCT task) as tasks_in_session
    GROUP BY sub, ses
""", format="json")
```


```python
q.run_query("""
    SELECT sub,
           COUNT(DISTINCT task) as unique_tasks,
           ARRAY_AGG(DISTINCT task) as completed_tasks,
           COUNT(*) as total_functional_files
    WHERE datatype=func
    GROUP BY sub
    HAVING COUNT(DISTINCT task) > 1  # Subjects with multiple tasks
""", format="json")
```

## Summary

You've learned how to:

1. **Basic queries**: Filter by BIDS entities
2. **Logical operators**: Combine conditions with AND, OR, NOT
3. **SELECT clause**: Choose specific fields to return
4. **Pattern matching**: Use wildcards and regex
5. **Ranges and lists**: Query multiple values efficiently
6. **Aggregations**: Count and group data
7. **Metadata queries**: Access JSON sidecar information
8. **Participant data**: Query demographics
9. **Complex queries**: Combine multiple features
10. **Output formats**: Export results in different formats

## Next Steps

- Check out the [Language Reference](language.md) for complete syntax details
- Explore more [examples](../examples/) for specific use cases
- Use the CLI tool `biql` for command-line queries
- Integrate BIQL into your Python analysis pipelines

Happy querying!
