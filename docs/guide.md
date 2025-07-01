---
title: BIQL Tutorial
nav_order: 3
---

# BIQL Tutorial

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/astewartau/biql/blob/main/docs/guide.ipynb)

This tutorial demonstrates how to use the BIDS Query Language (BIQL) to query neuroimaging datasets.
The examples below are automatically executed and updated whenever the documentation is built.

**Want to run this interactively?** Click the "Open in Colab" button above to run and modify the code yourself!


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
import sys

# Install BIQL if running in Colab
if 'google.colab' in sys.modules:
    !pip install git+https://github.com/astewartau/biql.git > /dev/null 2>&1
from biql import create_query_engine

# Set up paths - use a temporary directory that works in different environments
bids_examples_dir = Path(tempfile.gettempdir()) / "bids-examples"

# Clone bids-examples if it doesn't exist
if not bids_examples_dir.exists():
    !git clone https://github.com/bids-standard/bids-examples.git {bids_examples_dir} > /dev/null 2>&1
```

## Part 1: Basic Queries

Let's start with the synthetic dataset from bids-examples. This is a simple dataset
that's perfect for learning BIQL basics.


```python
dataset_path = bids_examples_dir / "synthetic"
q = create_query_engine(dataset_path)
q.dataset_stats()
```




    {'total_files': 60,
     'total_subjects': 5,
     'files_by_datatype': {'anat': 10, 'func': 30, 'beh': 5},
     'subjects': ['01', '02', '03', '04', '05'],
     'datatypes': ['anat', 'beh', 'func']}



### Simple Entity Queries

The most basic BIQL queries filter files by BIDS entities. You can query by any
BIDS entity that appears in your filenames:


```python
q.run_query("sub=01", format="dataframe").head(5)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>filepath</th>
      <th>relative_path</th>
      <th>filename</th>
      <th>sub</th>
      <th>ses</th>
      <th>suffix</th>
      <th>datatype</th>
      <th>extension</th>
      <th>metadata</th>
      <th>participants</th>
      <th>task</th>
      <th>run</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/ana...</td>
      <td>sub-01/ses-02/anat/sub-01_ses-02_T1w.nii</td>
      <td>sub-01_ses-02_T1w.nii</td>
      <td>01</td>
      <td>02</td>
      <td>T1w</td>
      <td>anat</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=34; sex=F</td>
      <td>NaN</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>1</th>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/fun...</td>
      <td>sub-01/ses-02/func/sub-01_ses-02_task-nback_ru...</td>
      <td>sub-01_ses-02_task-nback_run-02_bold.nii</td>
      <td>01</td>
      <td>02</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=34; sex=F</td>
      <td>nback</td>
      <td>02</td>
    </tr>
    <tr>
      <th>2</th>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/fun...</td>
      <td>sub-01/ses-02/func/sub-01_ses-02_task-nback_ru...</td>
      <td>sub-01_ses-02_task-nback_run-01_bold.nii</td>
      <td>01</td>
      <td>02</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=34; sex=F</td>
      <td>nback</td>
      <td>01</td>
    </tr>
    <tr>
      <th>3</th>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/fun...</td>
      <td>sub-01/ses-02/func/sub-01_ses-02_task-rest_bol...</td>
      <td>sub-01_ses-02_task-rest_bold.nii</td>
      <td>01</td>
      <td>02</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=34; sex=F</td>
      <td>rest</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>4</th>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-01/ana...</td>
      <td>sub-01/ses-01/anat/sub-01_ses-01_T1w.nii</td>
      <td>sub-01_ses-01_T1w.nii</td>
      <td>01</td>
      <td>01</td>
      <td>T1w</td>
      <td>anat</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=34; sex=F</td>
      <td>NaN</td>
      <td>NaN</td>
    </tr>
  </tbody>
</table>
</div>




```python
results = q.run_query("datatype=func")
len(results)  # Number of functional files
```




    30




```python
q.run_query("SELECT DISTINCT task WHERE datatype=func", format="dataframe")
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>task</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>nback</td>
    </tr>
    <tr>
      <th>1</th>
      <td>rest</td>
    </tr>
  </tbody>
</table>
</div>



### Combining Conditions

You can combine multiple conditions using AND, OR, and NOT operators:


```python
q.run_query("datatype=anat AND suffix=T1w", format="dataframe").head(5)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>filepath</th>
      <th>relative_path</th>
      <th>filename</th>
      <th>sub</th>
      <th>ses</th>
      <th>suffix</th>
      <th>datatype</th>
      <th>extension</th>
      <th>metadata</th>
      <th>participants</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/ana...</td>
      <td>sub-01/ses-02/anat/sub-01_ses-02_T1w.nii</td>
      <td>sub-01_ses-02_T1w.nii</td>
      <td>01</td>
      <td>02</td>
      <td>T1w</td>
      <td>anat</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=34; sex=F</td>
    </tr>
    <tr>
      <th>1</th>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-01/ana...</td>
      <td>sub-01/ses-01/anat/sub-01_ses-01_T1w.nii</td>
      <td>sub-01_ses-01_T1w.nii</td>
      <td>01</td>
      <td>01</td>
      <td>T1w</td>
      <td>anat</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=34; sex=F</td>
    </tr>
    <tr>
      <th>2</th>
      <td>/tmp/bids-examples/synthetic/sub-04/ses-02/ana...</td>
      <td>sub-04/ses-02/anat/sub-04_ses-02_T1w.nii</td>
      <td>sub-04_ses-02_T1w.nii</td>
      <td>04</td>
      <td>02</td>
      <td>T1w</td>
      <td>anat</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=21; sex=F</td>
    </tr>
    <tr>
      <th>3</th>
      <td>/tmp/bids-examples/synthetic/sub-04/ses-01/ana...</td>
      <td>sub-04/ses-01/anat/sub-04_ses-01_T1w.nii</td>
      <td>sub-04_ses-01_T1w.nii</td>
      <td>04</td>
      <td>01</td>
      <td>T1w</td>
      <td>anat</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=21; sex=F</td>
    </tr>
    <tr>
      <th>4</th>
      <td>/tmp/bids-examples/synthetic/sub-05/ses-02/ana...</td>
      <td>sub-05/ses-02/anat/sub-05_ses-02_T1w.nii</td>
      <td>sub-05_ses-02_T1w.nii</td>
      <td>05</td>
      <td>02</td>
      <td>T1w</td>
      <td>anat</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=42; sex=M</td>
    </tr>
  </tbody>
</table>
</div>




```python
q.run_query("task=nback OR task=rest", format="dataframe").head(5)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>filepath</th>
      <th>relative_path</th>
      <th>filename</th>
      <th>sub</th>
      <th>ses</th>
      <th>task</th>
      <th>run</th>
      <th>suffix</th>
      <th>datatype</th>
      <th>extension</th>
      <th>metadata</th>
      <th>participants</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/fun...</td>
      <td>sub-01/ses-02/func/sub-01_ses-02_task-nback_ru...</td>
      <td>sub-01_ses-02_task-nback_run-02_bold.nii</td>
      <td>01</td>
      <td>02</td>
      <td>nback</td>
      <td>02</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=34; sex=F</td>
    </tr>
    <tr>
      <th>1</th>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/fun...</td>
      <td>sub-01/ses-02/func/sub-01_ses-02_task-nback_ru...</td>
      <td>sub-01_ses-02_task-nback_run-01_bold.nii</td>
      <td>01</td>
      <td>02</td>
      <td>nback</td>
      <td>01</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=34; sex=F</td>
    </tr>
    <tr>
      <th>2</th>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/fun...</td>
      <td>sub-01/ses-02/func/sub-01_ses-02_task-rest_bol...</td>
      <td>sub-01_ses-02_task-rest_bold.nii</td>
      <td>01</td>
      <td>02</td>
      <td>rest</td>
      <td>NaN</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=34; sex=F</td>
    </tr>
    <tr>
      <th>3</th>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-01/fun...</td>
      <td>sub-01/ses-01/func/sub-01_ses-01_task-nback_ru...</td>
      <td>sub-01_ses-01_task-nback_run-02_bold.nii</td>
      <td>01</td>
      <td>01</td>
      <td>nback</td>
      <td>02</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=34; sex=F</td>
    </tr>
    <tr>
      <th>4</th>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-01/fun...</td>
      <td>sub-01/ses-01/func/sub-01_ses-01_task-rest_bol...</td>
      <td>sub-01_ses-01_task-rest_bold.nii</td>
      <td>01</td>
      <td>01</td>
      <td>rest</td>
      <td>NaN</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=34; sex=F</td>
    </tr>
  </tbody>
</table>
</div>



### Using WHERE Clause

For more SQL-like queries, you can use the WHERE clause:


```python
q.run_query("WHERE sub=01 AND datatype=func", format="dataframe")
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>filepath</th>
      <th>relative_path</th>
      <th>filename</th>
      <th>sub</th>
      <th>ses</th>
      <th>task</th>
      <th>run</th>
      <th>suffix</th>
      <th>datatype</th>
      <th>extension</th>
      <th>metadata</th>
      <th>participants</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/fun...</td>
      <td>sub-01/ses-02/func/sub-01_ses-02_task-nback_ru...</td>
      <td>sub-01_ses-02_task-nback_run-02_bold.nii</td>
      <td>01</td>
      <td>02</td>
      <td>nback</td>
      <td>02</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=34; sex=F</td>
    </tr>
    <tr>
      <th>1</th>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/fun...</td>
      <td>sub-01/ses-02/func/sub-01_ses-02_task-nback_ru...</td>
      <td>sub-01_ses-02_task-nback_run-01_bold.nii</td>
      <td>01</td>
      <td>02</td>
      <td>nback</td>
      <td>01</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=34; sex=F</td>
    </tr>
    <tr>
      <th>2</th>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/fun...</td>
      <td>sub-01/ses-02/func/sub-01_ses-02_task-rest_bol...</td>
      <td>sub-01_ses-02_task-rest_bold.nii</td>
      <td>01</td>
      <td>02</td>
      <td>rest</td>
      <td>NaN</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=34; sex=F</td>
    </tr>
    <tr>
      <th>3</th>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-01/fun...</td>
      <td>sub-01/ses-01/func/sub-01_ses-01_task-nback_ru...</td>
      <td>sub-01_ses-01_task-nback_run-02_bold.nii</td>
      <td>01</td>
      <td>01</td>
      <td>nback</td>
      <td>02</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=34; sex=F</td>
    </tr>
    <tr>
      <th>4</th>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-01/fun...</td>
      <td>sub-01/ses-01/func/sub-01_ses-01_task-rest_bol...</td>
      <td>sub-01_ses-01_task-rest_bold.nii</td>
      <td>01</td>
      <td>01</td>
      <td>rest</td>
      <td>NaN</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=34; sex=F</td>
    </tr>
    <tr>
      <th>5</th>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-01/fun...</td>
      <td>sub-01/ses-01/func/sub-01_ses-01_task-nback_ru...</td>
      <td>sub-01_ses-01_task-nback_run-01_bold.nii</td>
      <td>01</td>
      <td>01</td>
      <td>nback</td>
      <td>01</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=34; sex=F</td>
    </tr>
  </tbody>
</table>
</div>



## Part 2: SELECT Clause and Field Selection

By default, BIQL returns all available fields. Use SELECT to choose specific fields:


```python
q.run_query(
    "SELECT sub, task, run, filename WHERE datatype=func",
    format="dataframe"
).head(5)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>sub</th>
      <th>task</th>
      <th>run</th>
      <th>filename</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>01</td>
      <td>nback</td>
      <td>02</td>
      <td>sub-01_ses-02_task-nback_run-02_bold.nii</td>
    </tr>
    <tr>
      <th>1</th>
      <td>01</td>
      <td>nback</td>
      <td>01</td>
      <td>sub-01_ses-02_task-nback_run-01_bold.nii</td>
    </tr>
    <tr>
      <th>2</th>
      <td>01</td>
      <td>rest</td>
      <td>None</td>
      <td>sub-01_ses-02_task-rest_bold.nii</td>
    </tr>
    <tr>
      <th>3</th>
      <td>01</td>
      <td>nback</td>
      <td>02</td>
      <td>sub-01_ses-01_task-nback_run-02_bold.nii</td>
    </tr>
    <tr>
      <th>4</th>
      <td>01</td>
      <td>rest</td>
      <td>None</td>
      <td>sub-01_ses-01_task-rest_bold.nii</td>
    </tr>
  </tbody>
</table>
</div>




```python
q.run_query(
    "SELECT sub, relative_path WHERE suffix=T1w",
    format="dataframe"
)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>sub</th>
      <th>relative_path</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>01</td>
      <td>sub-01/ses-02/anat/sub-01_ses-02_T1w.nii</td>
    </tr>
    <tr>
      <th>1</th>
      <td>01</td>
      <td>sub-01/ses-01/anat/sub-01_ses-01_T1w.nii</td>
    </tr>
    <tr>
      <th>2</th>
      <td>04</td>
      <td>sub-04/ses-02/anat/sub-04_ses-02_T1w.nii</td>
    </tr>
    <tr>
      <th>3</th>
      <td>04</td>
      <td>sub-04/ses-01/anat/sub-04_ses-01_T1w.nii</td>
    </tr>
    <tr>
      <th>4</th>
      <td>05</td>
      <td>sub-05/ses-02/anat/sub-05_ses-02_T1w.nii</td>
    </tr>
    <tr>
      <th>5</th>
      <td>05</td>
      <td>sub-05/ses-01/anat/sub-05_ses-01_T1w.nii</td>
    </tr>
    <tr>
      <th>6</th>
      <td>02</td>
      <td>sub-02/ses-02/anat/sub-02_ses-02_T1w.nii</td>
    </tr>
    <tr>
      <th>7</th>
      <td>02</td>
      <td>sub-02/ses-01/anat/sub-02_ses-01_T1w.nii</td>
    </tr>
    <tr>
      <th>8</th>
      <td>03</td>
      <td>sub-03/ses-02/anat/sub-03_ses-02_T1w.nii</td>
    </tr>
    <tr>
      <th>9</th>
      <td>03</td>
      <td>sub-03/ses-01/anat/sub-03_ses-01_T1w.nii</td>
    </tr>
  </tbody>
</table>
</div>



## Part 3: Pattern Matching

BIQL supports wildcards and regular expressions for flexible matching:


```python
results = q.run_query("suffix=*bold*")
len(results)  # Count of files with 'bold' in suffix
```




    30




```python
q.run_query(
    "SELECT DISTINCT task WHERE task~=\".*back*\"",
    format="dataframe"
)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>task</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>nback</td>
    </tr>
  </tbody>
</table>
</div>



## Part 4: Ranges and Lists

BIQL supports convenient syntax for matching multiple values and ranges:

### List Matching with IN

Use `IN` to match any value from a list:


```python
# Find files for specific subjects
q.run_query(
    "SELECT sub, task, filename WHERE sub IN ['01', '02', '03'] AND datatype=func",
    format="dataframe"
).head()
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>sub</th>
      <th>task</th>
      <th>filename</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>01</td>
      <td>nback</td>
      <td>sub-01_ses-02_task-nback_run-02_bold.nii</td>
    </tr>
    <tr>
      <th>1</th>
      <td>01</td>
      <td>nback</td>
      <td>sub-01_ses-02_task-nback_run-01_bold.nii</td>
    </tr>
    <tr>
      <th>2</th>
      <td>01</td>
      <td>rest</td>
      <td>sub-01_ses-02_task-rest_bold.nii</td>
    </tr>
    <tr>
      <th>3</th>
      <td>01</td>
      <td>nback</td>
      <td>sub-01_ses-01_task-nback_run-02_bold.nii</td>
    </tr>
    <tr>
      <th>4</th>
      <td>01</td>
      <td>rest</td>
      <td>sub-01_ses-01_task-rest_bold.nii</td>
    </tr>
  </tbody>
</table>
</div>




```python
# Find specific tasks
q.run_query(
    "SELECT DISTINCT sub WHERE task IN ['nback', 'rest']",
    format="dataframe"
)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>sub</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>01</td>
    </tr>
    <tr>
      <th>1</th>
      <td>04</td>
    </tr>
    <tr>
      <th>2</th>
      <td>05</td>
    </tr>
    <tr>
      <th>3</th>
      <td>02</td>
    </tr>
    <tr>
      <th>4</th>
      <td>03</td>
    </tr>
  </tbody>
</table>
</div>




```python
# Combining lists and other conditions  
q.run_query(
    "SELECT sub, COUNT(*) as file_count "
    "WHERE sub IN ['01', '02'] AND task IN ['nback', 'rest'] "
    "GROUP BY sub",
    format="dataframe"
)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>sub</th>
      <th>file_count</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>01</td>
      <td>6</td>
    </tr>
    <tr>
      <th>1</th>
      <td>02</td>
      <td>6</td>
    </tr>
  </tbody>
</table>
</div>



### Range Matching

Use `[start:end]` syntax for numeric ranges (inclusive):


```python
# Find runs 1 and 2 (inclusive range)
q.run_query(
    "SELECT sub, task, run WHERE run=[1:2] AND datatype=func",
    format="dataframe"
)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>sub</th>
      <th>task</th>
      <th>run</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>01</td>
      <td>nback</td>
      <td>02</td>
    </tr>
    <tr>
      <th>1</th>
      <td>01</td>
      <td>nback</td>
      <td>01</td>
    </tr>
    <tr>
      <th>2</th>
      <td>01</td>
      <td>nback</td>
      <td>02</td>
    </tr>
    <tr>
      <th>3</th>
      <td>01</td>
      <td>nback</td>
      <td>01</td>
    </tr>
    <tr>
      <th>4</th>
      <td>04</td>
      <td>nback</td>
      <td>02</td>
    </tr>
    <tr>
      <th>5</th>
      <td>04</td>
      <td>nback</td>
      <td>01</td>
    </tr>
    <tr>
      <th>6</th>
      <td>04</td>
      <td>nback</td>
      <td>02</td>
    </tr>
    <tr>
      <th>7</th>
      <td>04</td>
      <td>nback</td>
      <td>01</td>
    </tr>
    <tr>
      <th>8</th>
      <td>05</td>
      <td>nback</td>
      <td>02</td>
    </tr>
    <tr>
      <th>9</th>
      <td>05</td>
      <td>nback</td>
      <td>01</td>
    </tr>
    <tr>
      <th>10</th>
      <td>05</td>
      <td>nback</td>
      <td>02</td>
    </tr>
    <tr>
      <th>11</th>
      <td>05</td>
      <td>nback</td>
      <td>01</td>
    </tr>
    <tr>
      <th>12</th>
      <td>02</td>
      <td>nback</td>
      <td>02</td>
    </tr>
    <tr>
      <th>13</th>
      <td>02</td>
      <td>nback</td>
      <td>01</td>
    </tr>
    <tr>
      <th>14</th>
      <td>02</td>
      <td>nback</td>
      <td>02</td>
    </tr>
    <tr>
      <th>15</th>
      <td>02</td>
      <td>nback</td>
      <td>01</td>
    </tr>
    <tr>
      <th>16</th>
      <td>03</td>
      <td>nback</td>
      <td>01</td>
    </tr>
    <tr>
      <th>17</th>
      <td>03</td>
      <td>nback</td>
      <td>02</td>
    </tr>
    <tr>
      <th>18</th>
      <td>03</td>
      <td>nback</td>
      <td>02</td>
    </tr>
    <tr>
      <th>19</th>
      <td>03</td>
      <td>nback</td>
      <td>01</td>
    </tr>
  </tbody>
</table>
</div>



## Part 5: Grouping and Aggregation

BIQL supports SQL-like grouping and aggregation functions:


```python
q.run_query("SELECT sub, COUNT(*) GROUP BY sub", format="dataframe")
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>sub</th>
      <th>count</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>01</td>
      <td>12</td>
    </tr>
    <tr>
      <th>1</th>
      <td>04</td>
      <td>12</td>
    </tr>
    <tr>
      <th>2</th>
      <td>05</td>
      <td>12</td>
    </tr>
    <tr>
      <th>3</th>
      <td>02</td>
      <td>12</td>
    </tr>
    <tr>
      <th>4</th>
      <td>03</td>
      <td>12</td>
    </tr>
  </tbody>
</table>
</div>




```python
q.run_query(
    "SELECT sub, datatype, COUNT(*) GROUP BY sub, datatype",
    format="json"
)
```




    [{'sub': '01', 'datatype': 'anat', 'count': 2},
     {'sub': '01', 'datatype': 'func', 'count': 6},
     {'sub': '04', 'datatype': 'anat', 'count': 2},
     {'sub': '04', 'datatype': 'func', 'count': 6},
     {'sub': '05', 'datatype': 'anat', 'count': 2},
     {'sub': '05', 'datatype': 'func', 'count': 6},
     {'sub': '02', 'datatype': 'anat', 'count': 2},
     {'sub': '02', 'datatype': 'func', 'count': 6},
     {'sub': '03', 'datatype': 'anat', 'count': 2},
     {'sub': '03', 'datatype': 'func', 'count': 6},
     {'sub': '01', 'datatype': None, 'count': 3},
     {'sub': '01', 'datatype': 'beh', 'count': 1},
     {'sub': '04', 'datatype': None, 'count': 3},
     {'sub': '04', 'datatype': 'beh', 'count': 1},
     {'sub': '05', 'datatype': None, 'count': 3},
     {'sub': '05', 'datatype': 'beh', 'count': 1},
     {'sub': '02', 'datatype': None, 'count': 3},
     {'sub': '02', 'datatype': 'beh', 'count': 1},
     {'sub': '03', 'datatype': None, 'count': 3},
     {'sub': '03', 'datatype': 'beh', 'count': 1}]




```python
# Compare DISTINCT vs non-DISTINCT - get all task names (including duplicates)
q.run_query(
    "SELECT sub, (task) as all_task_names, (DISTINCT task) as unique_tasks "
    "WHERE sub='01' "
    "GROUP BY sub",
    format="json"
)
```




    [{'sub': '01',
      'all_task_names': ['nback',
       'nback',
       'nback',
       'nback',
       'rest',
       'rest',
       'stroop',
       None,
       None,
       None,
       None,
       None],
      'unique_tasks': ['nback', 'rest', 'stroop']}]




```python
# Get unique tasks per subject
q.run_query(
    "SELECT sub, (DISTINCT task) as unique_tasks, COUNT(*) as total_files "
    "WHERE sub IN ['01', '02', '03'] "
    "GROUP BY sub",
    format="json"
)
```




    [{'sub': '01', 'unique_tasks': ['nback', 'rest', 'stroop'], 'total_files': 12},
     {'sub': '02', 'unique_tasks': ['nback', 'rest', 'stroop'], 'total_files': 12},
     {'sub': '03', 'unique_tasks': ['nback', 'rest', 'stroop'], 'total_files': 12}]



### Array Aggregation with DISTINCT

BIQL supports collecting values into arrays using the `(field)` syntax:

- `(DISTINCT field)` returns unique non-null values  
- `(field)` returns all values including duplicates

## Part 6: Working with Metadata

BIQL can query JSON sidecar metadata using the `metadata.` namespace. 
Let's explore a more complex dataset to see this in action:


```python
# Switch to a dataset with more metadata  
ds2_path = bids_examples_dir / "ds000117"
q2 = create_query_engine(ds2_path) if (bids_examples_dir / "ds000117").exists() else q

# Show what metadata fields are available
q2.run_query(
    "SELECT DISTINCT task WHERE datatype=func",
    format="dataframe"
)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>task</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>facerecognition</td>
    </tr>
  </tbody>
</table>
</div>




```python
# For the synthetic dataset, we can still demonstrate basic grouping by task
q.run_query(
    "SELECT task, COUNT(*) as file_count, "
    "COUNT(DISTINCT sub) as subjects "
    "GROUP BY task",
    format="dataframe"
)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>task</th>
      <th>file_count</th>
      <th>subjects</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>None</td>
      <td>25</td>
      <td>5</td>
    </tr>
    <tr>
      <th>1</th>
      <td>nback</td>
      <td>20</td>
      <td>5</td>
    </tr>
    <tr>
      <th>2</th>
      <td>rest</td>
      <td>10</td>
      <td>5</td>
    </tr>
    <tr>
      <th>3</th>
      <td>stroop</td>
      <td>5</td>
      <td>5</td>
    </tr>
  </tbody>
</table>
</div>



## Part 7: Participant Information

Access participant demographics using the `participants.` namespace:


```python
q.run_query(
    "SELECT DISTINCT sub, participants.age, participants.sex",
    format="dataframe"
)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>sub</th>
      <th>participants.age</th>
      <th>participants.sex</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>01</td>
      <td>34</td>
      <td>F</td>
    </tr>
    <tr>
      <th>1</th>
      <td>04</td>
      <td>21</td>
      <td>F</td>
    </tr>
    <tr>
      <th>2</th>
      <td>05</td>
      <td>42</td>
      <td>M</td>
    </tr>
    <tr>
      <th>3</th>
      <td>02</td>
      <td>38</td>
      <td>M</td>
    </tr>
    <tr>
      <th>4</th>
      <td>03</td>
      <td>22</td>
      <td>M</td>
    </tr>
  </tbody>
</table>
</div>




```python
q.run_query(
    "SELECT sub, task, participants.age WHERE participants.age > 25",
    format="dataframe"
)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>sub</th>
      <th>task</th>
      <th>participants.age</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>01</td>
      <td>None</td>
      <td>34</td>
    </tr>
    <tr>
      <th>1</th>
      <td>01</td>
      <td>nback</td>
      <td>34</td>
    </tr>
    <tr>
      <th>2</th>
      <td>01</td>
      <td>nback</td>
      <td>34</td>
    </tr>
    <tr>
      <th>3</th>
      <td>01</td>
      <td>rest</td>
      <td>34</td>
    </tr>
    <tr>
      <th>4</th>
      <td>01</td>
      <td>None</td>
      <td>34</td>
    </tr>
    <tr>
      <th>5</th>
      <td>01</td>
      <td>nback</td>
      <td>34</td>
    </tr>
    <tr>
      <th>6</th>
      <td>01</td>
      <td>rest</td>
      <td>34</td>
    </tr>
    <tr>
      <th>7</th>
      <td>01</td>
      <td>nback</td>
      <td>34</td>
    </tr>
    <tr>
      <th>8</th>
      <td>05</td>
      <td>None</td>
      <td>42</td>
    </tr>
    <tr>
      <th>9</th>
      <td>05</td>
      <td>rest</td>
      <td>42</td>
    </tr>
    <tr>
      <th>10</th>
      <td>05</td>
      <td>nback</td>
      <td>42</td>
    </tr>
    <tr>
      <th>11</th>
      <td>05</td>
      <td>nback</td>
      <td>42</td>
    </tr>
    <tr>
      <th>12</th>
      <td>05</td>
      <td>None</td>
      <td>42</td>
    </tr>
    <tr>
      <th>13</th>
      <td>05</td>
      <td>nback</td>
      <td>42</td>
    </tr>
    <tr>
      <th>14</th>
      <td>05</td>
      <td>rest</td>
      <td>42</td>
    </tr>
    <tr>
      <th>15</th>
      <td>05</td>
      <td>nback</td>
      <td>42</td>
    </tr>
    <tr>
      <th>16</th>
      <td>02</td>
      <td>None</td>
      <td>38</td>
    </tr>
    <tr>
      <th>17</th>
      <td>02</td>
      <td>rest</td>
      <td>38</td>
    </tr>
    <tr>
      <th>18</th>
      <td>02</td>
      <td>nback</td>
      <td>38</td>
    </tr>
    <tr>
      <th>19</th>
      <td>02</td>
      <td>nback</td>
      <td>38</td>
    </tr>
    <tr>
      <th>20</th>
      <td>02</td>
      <td>None</td>
      <td>38</td>
    </tr>
    <tr>
      <th>21</th>
      <td>02</td>
      <td>nback</td>
      <td>38</td>
    </tr>
    <tr>
      <th>22</th>
      <td>02</td>
      <td>nback</td>
      <td>38</td>
    </tr>
    <tr>
      <th>23</th>
      <td>02</td>
      <td>rest</td>
      <td>38</td>
    </tr>
    <tr>
      <th>24</th>
      <td>01</td>
      <td>None</td>
      <td>34</td>
    </tr>
    <tr>
      <th>25</th>
      <td>01</td>
      <td>None</td>
      <td>34</td>
    </tr>
    <tr>
      <th>26</th>
      <td>01</td>
      <td>None</td>
      <td>34</td>
    </tr>
    <tr>
      <th>27</th>
      <td>01</td>
      <td>stroop</td>
      <td>34</td>
    </tr>
    <tr>
      <th>28</th>
      <td>05</td>
      <td>None</td>
      <td>42</td>
    </tr>
    <tr>
      <th>29</th>
      <td>05</td>
      <td>None</td>
      <td>42</td>
    </tr>
    <tr>
      <th>30</th>
      <td>05</td>
      <td>None</td>
      <td>42</td>
    </tr>
    <tr>
      <th>31</th>
      <td>05</td>
      <td>stroop</td>
      <td>42</td>
    </tr>
    <tr>
      <th>32</th>
      <td>02</td>
      <td>None</td>
      <td>38</td>
    </tr>
    <tr>
      <th>33</th>
      <td>02</td>
      <td>None</td>
      <td>38</td>
    </tr>
    <tr>
      <th>34</th>
      <td>02</td>
      <td>None</td>
      <td>38</td>
    </tr>
    <tr>
      <th>35</th>
      <td>02</td>
      <td>stroop</td>
      <td>38</td>
    </tr>
  </tbody>
</table>
</div>



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




    [{'sub': '01', 'ses': '02', 'task': 'nback', 'n_runs': 2},
     {'sub': '01', 'ses': '01', 'task': 'nback', 'n_runs': 2},
     {'sub': '02', 'ses': '02', 'task': 'nback', 'n_runs': 2},
     {'sub': '02', 'ses': '01', 'task': 'nback', 'n_runs': 2},
     {'sub': '03', 'ses': '02', 'task': 'nback', 'n_runs': 2},
     {'sub': '03', 'ses': '01', 'task': 'nback', 'n_runs': 2},
     {'sub': '04', 'ses': '02', 'task': 'nback', 'n_runs': 2},
     {'sub': '04', 'ses': '01', 'task': 'nback', 'n_runs': 2},
     {'sub': '05', 'ses': '02', 'task': 'nback', 'n_runs': 2},
     {'sub': '05', 'ses': '01', 'task': 'nback', 'n_runs': 2}]




```python
q.run_query("""
    SELECT sub, task,
           (filename WHERE suffix='bold') as imaging_files,
           (filename WHERE run='01') as run01_files,
           (filename WHERE run='02') as run02_files
    WHERE datatype=func
    GROUP BY sub, task
""", format="table")  # Using table format since arrays don't display well in dataframes
```




    '| imaging_files   | run01_files     | run02_files     | sub | task  |\n| --------------- | --------------- | --------------- | --- | ----- |\n| [...4 items...] | [...2 items...] | [...2 items...] | 01  | nback |\n| [...2 items...] | [...0 items...] | [...0 items...] | 01  | rest  |\n| [...4 items...] | [...2 items...] | [...2 items...] | 04  | nback |\n| [...2 items...] | [...0 items...] | [...0 items...] | 04  | rest  |\n| [...2 items...] | [...0 items...] | [...0 items...] | 05  | rest  |\n| [...4 items...] | [...2 items...] | [...2 items...] | 05  | nback |\n| [...2 items...] | [...0 items...] | [...0 items...] | 02  | rest  |\n| [...4 items...] | [...2 items...] | [...2 items...] | 02  | nback |\n| [...4 items...] | [...2 items...] | [...2 items...] | 03  | nback |\n| [...2 items...] | [...0 items...] | [...0 items...] | 03  | rest  |'



## Part 9: Output Formats

BIQL supports multiple output formats for different use cases:


```python
sample_query = "SELECT sub, task, run WHERE datatype=func AND sub=01"

print(q.run_query(sample_query, format="table"))
```

    | run | sub | task  |
    | --- | --- | ----- |
    | 02  | 01  | nback |
    | 01  | 01  | nback |
    |     | 01  | rest  |
    | 02  | 01  | nback |
    |     | 01  | rest  |
    | 01  | 01  | nback |



```python
print(q.run_query(sample_query, format="csv"))
```

    run,sub,task
    02,01,nback
    01,01,nback
    ,01,rest
    02,01,nback
    ,01,rest
    01,01,nback
    



```python
results_json = q.run_query(sample_query, format="json")
results_json[:2]  # Show first 2 entries
```




    [{'sub': '01', 'task': 'nback', 'run': '02'},
     {'sub': '01', 'task': 'nback', 'run': '01'}]




```python
print(q.run_query("WHERE sub=01 AND suffix=T1w", format="paths"))
```

    /tmp/bids-examples/synthetic/sub-01/ses-01/anat/sub-01_ses-01_T1w.nii
    /tmp/bids-examples/synthetic/sub-01/ses-02/anat/sub-01_ses-02_T1w.nii



```python
q.run_query(sample_query, format="dataframe")
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>sub</th>
      <th>task</th>
      <th>run</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>01</td>
      <td>nback</td>
      <td>02</td>
    </tr>
    <tr>
      <th>1</th>
      <td>01</td>
      <td>nback</td>
      <td>01</td>
    </tr>
    <tr>
      <th>2</th>
      <td>01</td>
      <td>rest</td>
      <td>None</td>
    </tr>
    <tr>
      <th>3</th>
      <td>01</td>
      <td>nback</td>
      <td>02</td>
    </tr>
    <tr>
      <th>4</th>
      <td>01</td>
      <td>rest</td>
      <td>None</td>
    </tr>
    <tr>
      <th>5</th>
      <td>01</td>
      <td>nback</td>
      <td>01</td>
    </tr>
  </tbody>
</table>
</div>



## Part 10: Real-World Examples

Let's look at some practical queries you might use in neuroimaging research:


```python
q.run_query("""
    SELECT sub, 
           COUNT(*) as total_files,
           COUNT(DISTINCT datatype) as datatypes,
           (DISTINCT datatype) as available_data
    GROUP BY sub
""", format="json")
```




    [{'sub': '01',
      'total_files': 12,
      'datatypes': 3,
      'available_data': ['anat', 'beh', 'func']},
     {'sub': '04',
      'total_files': 12,
      'datatypes': 3,
      'available_data': ['anat', 'beh', 'func']},
     {'sub': '05',
      'total_files': 12,
      'datatypes': 3,
      'available_data': ['anat', 'beh', 'func']},
     {'sub': '02',
      'total_files': 12,
      'datatypes': 3,
      'available_data': ['anat', 'beh', 'func']},
     {'sub': '03',
      'total_files': 12,
      'datatypes': 3,
      'available_data': ['anat', 'beh', 'func']}]




```python
q.run_query("""
    SELECT sub, ses,
           COUNT(*) as files_per_session,
           (DISTINCT task) as tasks_in_session
    GROUP BY sub, ses
""", format="json")
```




    [{'sub': '01',
      'ses': '02',
      'files_per_session': 5,
      'tasks_in_session': ['nback', 'rest']},
     {'sub': '01',
      'ses': '01',
      'files_per_session': 6,
      'tasks_in_session': ['nback', 'rest', 'stroop']},
     {'sub': '04',
      'ses': '02',
      'files_per_session': 5,
      'tasks_in_session': ['nback', 'rest']},
     {'sub': '04',
      'ses': '01',
      'files_per_session': 6,
      'tasks_in_session': ['nback', 'rest', 'stroop']},
     {'sub': '05',
      'ses': '02',
      'files_per_session': 5,
      'tasks_in_session': ['nback', 'rest']},
     {'sub': '05',
      'ses': '01',
      'files_per_session': 6,
      'tasks_in_session': ['nback', 'rest', 'stroop']},
     {'sub': '02',
      'ses': '02',
      'files_per_session': 5,
      'tasks_in_session': ['nback', 'rest']},
     {'sub': '02',
      'ses': '01',
      'files_per_session': 6,
      'tasks_in_session': ['nback', 'rest', 'stroop']},
     {'sub': '03',
      'ses': '02',
      'files_per_session': 5,
      'tasks_in_session': ['nback', 'rest']},
     {'sub': '03',
      'ses': '01',
      'files_per_session': 6,
      'tasks_in_session': ['nback', 'rest', 'stroop']},
     {'sub': '01', 'ses': None, 'files_per_session': 1, 'tasks_in_session': []},
     {'sub': '04', 'ses': None, 'files_per_session': 1, 'tasks_in_session': []},
     {'sub': '05', 'ses': None, 'files_per_session': 1, 'tasks_in_session': []},
     {'sub': '02', 'ses': None, 'files_per_session': 1, 'tasks_in_session': []},
     {'sub': '03', 'ses': None, 'files_per_session': 1, 'tasks_in_session': []}]




```python
q.run_query("""
    SELECT sub,
           COUNT(DISTINCT task) as unique_tasks,
           (DISTINCT task) as completed_tasks,
           COUNT(*) as total_functional_files
    WHERE datatype=func
    GROUP BY sub
    HAVING COUNT(DISTINCT task) > 1  # Subjects with multiple tasks
""", format="json")
```




    [{'sub': '01',
      'unique_tasks': 2,
      'completed_tasks': ['nback', 'rest'],
      'total_functional_files': 6},
     {'sub': '04',
      'unique_tasks': 2,
      'completed_tasks': ['nback', 'rest'],
      'total_functional_files': 6},
     {'sub': '05',
      'unique_tasks': 2,
      'completed_tasks': ['nback', 'rest'],
      'total_functional_files': 6},
     {'sub': '02',
      'unique_tasks': 2,
      'completed_tasks': ['nback', 'rest'],
      'total_functional_files': 6},
     {'sub': '03',
      'unique_tasks': 2,
      'completed_tasks': ['nback', 'rest'],
      'total_functional_files': 6}]


