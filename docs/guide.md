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
from biql import create_query_engine
import sys

# Install BIQL if running in Colab
if 'google.colab' in sys.modules:
    !pip install git+https://github.com/astewartau/biql.git > /dev/null 2>&1

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
      <th>_file_paths</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>nback</td>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/fun...</td>
    </tr>
    <tr>
      <th>1</th>
      <td>rest</td>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/fun...</td>
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
      <th>filename</th>
      <th>_file_paths</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>01</td>
      <td>nback</td>
      <td>02</td>
      <td>sub-01_ses-02_task-nback_run-02_bold.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/fun...</td>
    </tr>
    <tr>
      <th>1</th>
      <td>01</td>
      <td>nback</td>
      <td>01</td>
      <td>sub-01_ses-02_task-nback_run-01_bold.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/fun...</td>
    </tr>
    <tr>
      <th>2</th>
      <td>01</td>
      <td>rest</td>
      <td>None</td>
      <td>sub-01_ses-02_task-rest_bold.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/fun...</td>
    </tr>
    <tr>
      <th>3</th>
      <td>01</td>
      <td>nback</td>
      <td>02</td>
      <td>sub-01_ses-01_task-nback_run-02_bold.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-01/fun...</td>
    </tr>
    <tr>
      <th>4</th>
      <td>01</td>
      <td>rest</td>
      <td>None</td>
      <td>sub-01_ses-01_task-rest_bold.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-01/fun...</td>
    </tr>
    <tr>
      <th>5</th>
      <td>01</td>
      <td>nback</td>
      <td>01</td>
      <td>sub-01_ses-01_task-nback_run-01_bold.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-01/fun...</td>
    </tr>
    <tr>
      <th>6</th>
      <td>04</td>
      <td>nback</td>
      <td>02</td>
      <td>sub-04_ses-02_task-nback_run-02_bold.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-04/ses-02/fun...</td>
    </tr>
    <tr>
      <th>7</th>
      <td>04</td>
      <td>nback</td>
      <td>01</td>
      <td>sub-04_ses-02_task-nback_run-01_bold.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-04/ses-02/fun...</td>
    </tr>
    <tr>
      <th>8</th>
      <td>04</td>
      <td>rest</td>
      <td>None</td>
      <td>sub-04_ses-02_task-rest_bold.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-04/ses-02/fun...</td>
    </tr>
    <tr>
      <th>9</th>
      <td>04</td>
      <td>nback</td>
      <td>02</td>
      <td>sub-04_ses-01_task-nback_run-02_bold.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-04/ses-01/fun...</td>
    </tr>
    <tr>
      <th>10</th>
      <td>04</td>
      <td>rest</td>
      <td>None</td>
      <td>sub-04_ses-01_task-rest_bold.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-04/ses-01/fun...</td>
    </tr>
    <tr>
      <th>11</th>
      <td>04</td>
      <td>nback</td>
      <td>01</td>
      <td>sub-04_ses-01_task-nback_run-01_bold.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-04/ses-01/fun...</td>
    </tr>
    <tr>
      <th>12</th>
      <td>05</td>
      <td>rest</td>
      <td>None</td>
      <td>sub-05_ses-02_task-rest_bold.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-05/ses-02/fun...</td>
    </tr>
    <tr>
      <th>13</th>
      <td>05</td>
      <td>nback</td>
      <td>02</td>
      <td>sub-05_ses-02_task-nback_run-02_bold.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-05/ses-02/fun...</td>
    </tr>
    <tr>
      <th>14</th>
      <td>05</td>
      <td>nback</td>
      <td>01</td>
      <td>sub-05_ses-02_task-nback_run-01_bold.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-05/ses-02/fun...</td>
    </tr>
    <tr>
      <th>15</th>
      <td>05</td>
      <td>nback</td>
      <td>02</td>
      <td>sub-05_ses-01_task-nback_run-02_bold.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-05/ses-01/fun...</td>
    </tr>
    <tr>
      <th>16</th>
      <td>05</td>
      <td>rest</td>
      <td>None</td>
      <td>sub-05_ses-01_task-rest_bold.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-05/ses-01/fun...</td>
    </tr>
    <tr>
      <th>17</th>
      <td>05</td>
      <td>nback</td>
      <td>01</td>
      <td>sub-05_ses-01_task-nback_run-01_bold.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-05/ses-01/fun...</td>
    </tr>
    <tr>
      <th>18</th>
      <td>02</td>
      <td>rest</td>
      <td>None</td>
      <td>sub-02_ses-02_task-rest_bold.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-02/ses-02/fun...</td>
    </tr>
    <tr>
      <th>19</th>
      <td>02</td>
      <td>nback</td>
      <td>02</td>
      <td>sub-02_ses-02_task-nback_run-02_bold.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-02/ses-02/fun...</td>
    </tr>
    <tr>
      <th>20</th>
      <td>02</td>
      <td>nback</td>
      <td>01</td>
      <td>sub-02_ses-02_task-nback_run-01_bold.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-02/ses-02/fun...</td>
    </tr>
    <tr>
      <th>21</th>
      <td>02</td>
      <td>nback</td>
      <td>02</td>
      <td>sub-02_ses-01_task-nback_run-02_bold.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-02/ses-01/fun...</td>
    </tr>
    <tr>
      <th>22</th>
      <td>02</td>
      <td>nback</td>
      <td>01</td>
      <td>sub-02_ses-01_task-nback_run-01_bold.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-02/ses-01/fun...</td>
    </tr>
    <tr>
      <th>23</th>
      <td>02</td>
      <td>rest</td>
      <td>None</td>
      <td>sub-02_ses-01_task-rest_bold.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-02/ses-01/fun...</td>
    </tr>
    <tr>
      <th>24</th>
      <td>03</td>
      <td>nback</td>
      <td>01</td>
      <td>sub-03_ses-02_task-nback_run-01_bold.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-03/ses-02/fun...</td>
    </tr>
    <tr>
      <th>25</th>
      <td>03</td>
      <td>nback</td>
      <td>02</td>
      <td>sub-03_ses-02_task-nback_run-02_bold.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-03/ses-02/fun...</td>
    </tr>
    <tr>
      <th>26</th>
      <td>03</td>
      <td>rest</td>
      <td>None</td>
      <td>sub-03_ses-02_task-rest_bold.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-03/ses-02/fun...</td>
    </tr>
    <tr>
      <th>27</th>
      <td>03</td>
      <td>rest</td>
      <td>None</td>
      <td>sub-03_ses-01_task-rest_bold.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-03/ses-01/fun...</td>
    </tr>
    <tr>
      <th>28</th>
      <td>03</td>
      <td>nback</td>
      <td>02</td>
      <td>sub-03_ses-01_task-nback_run-02_bold.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-03/ses-01/fun...</td>
    </tr>
    <tr>
      <th>29</th>
      <td>03</td>
      <td>nback</td>
      <td>01</td>
      <td>sub-03_ses-01_task-nback_run-01_bold.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-03/ses-01/fun...</td>
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
      <th>_file_paths</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>01</td>
      <td>sub-01/ses-02/anat/sub-01_ses-02_T1w.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/ana...</td>
    </tr>
    <tr>
      <th>1</th>
      <td>01</td>
      <td>sub-01/ses-01/anat/sub-01_ses-01_T1w.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-01/ana...</td>
    </tr>
    <tr>
      <th>2</th>
      <td>04</td>
      <td>sub-04/ses-02/anat/sub-04_ses-02_T1w.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-04/ses-02/ana...</td>
    </tr>
    <tr>
      <th>3</th>
      <td>04</td>
      <td>sub-04/ses-01/anat/sub-04_ses-01_T1w.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-04/ses-01/ana...</td>
    </tr>
    <tr>
      <th>4</th>
      <td>05</td>
      <td>sub-05/ses-02/anat/sub-05_ses-02_T1w.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-05/ses-02/ana...</td>
    </tr>
    <tr>
      <th>5</th>
      <td>05</td>
      <td>sub-05/ses-01/anat/sub-05_ses-01_T1w.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-05/ses-01/ana...</td>
    </tr>
    <tr>
      <th>6</th>
      <td>02</td>
      <td>sub-02/ses-02/anat/sub-02_ses-02_T1w.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-02/ses-02/ana...</td>
    </tr>
    <tr>
      <th>7</th>
      <td>02</td>
      <td>sub-02/ses-01/anat/sub-02_ses-01_T1w.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-02/ses-01/ana...</td>
    </tr>
    <tr>
      <th>8</th>
      <td>03</td>
      <td>sub-03/ses-02/anat/sub-03_ses-02_T1w.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-03/ses-02/ana...</td>
    </tr>
    <tr>
      <th>9</th>
      <td>03</td>
      <td>sub-03/ses-01/anat/sub-03_ses-01_T1w.nii</td>
      <td>/tmp/bids-examples/synthetic/sub-03/ses-01/ana...</td>
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
    "SELECT DISTINCT task WHERE task~=\".*back.*\"",
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
      <th>_file_paths</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>nback</td>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/fun...</td>
    </tr>
  </tbody>
</table>
</div>



## Part 4: Ranges and Lists

BIQL supports range queries and IN operators for matching multiple values:

### DISTINCT vs Non-DISTINCT Aggregations

BIQL supports both DISTINCT and non-DISTINCT array aggregations:

- **With DISTINCT**: `ARRAY_AGG(DISTINCT field)` returns only unique non-null values
- **Without DISTINCT**: `ARRAY_AGG(field)` returns all values including duplicates and nulls

The count of items in a non-DISTINCT array will match `COUNT(*)` for the group:


```python
q.run_query(
    "SELECT sub, ARRAY_AGG(DISTINCT task) as tasks, COUNT(*) as total_files "
    "WHERE sub IN ['01', '02', '03'] "
    "GROUP BY sub",
    format="json"
)
```




    [{'sub': '01',
      'tasks': ['nback', 'rest', 'stroop'],
      'total_files': 12,
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-01/ses-02/anat/sub-01_ses-02_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-02/func/sub-01_ses-02_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-02/func/sub-01_ses-02_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-02/func/sub-01_ses-02_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-01/anat/sub-01_ses-01_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-01/func/sub-01_ses-01_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-01/func/sub-01_ses-01_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-01/func/sub-01_ses-01_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/sub-01_sessions.tsv',
       '/tmp/bids-examples/synthetic/sub-01/ses-02/sub-01_ses-02_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-01/ses-01/sub-01_ses-01_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-01/ses-01/beh/sub-01_ses-01_task-stroop_beh.tsv']},
     {'sub': '02',
      'tasks': ['nback', 'rest', 'stroop'],
      'total_files': 12,
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-02/ses-02/anat/sub-02_ses-02_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-02/func/sub-02_ses-02_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-02/func/sub-02_ses-02_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-02/func/sub-02_ses-02_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-01/anat/sub-02_ses-01_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-01/func/sub-02_ses-01_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-01/func/sub-02_ses-01_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-01/func/sub-02_ses-01_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/sub-02_sessions.tsv',
       '/tmp/bids-examples/synthetic/sub-02/ses-02/sub-02_ses-02_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-02/ses-01/sub-02_ses-01_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-02/ses-01/beh/sub-02_ses-01_task-stroop_beh.tsv']},
     {'sub': '03',
      'tasks': ['nback', 'rest', 'stroop'],
      'total_files': 12,
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-03/ses-02/anat/sub-03_ses-02_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-02/func/sub-03_ses-02_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-02/func/sub-03_ses-02_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-02/func/sub-03_ses-02_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-01/anat/sub-03_ses-01_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-01/func/sub-03_ses-01_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-01/func/sub-03_ses-01_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-01/func/sub-03_ses-01_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/sub-03_sessions.tsv',
       '/tmp/bids-examples/synthetic/sub-03/ses-02/sub-03_ses-02_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-03/ses-01/sub-03_ses-01_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-03/ses-01/beh/sub-03_ses-01_task-stroop_beh.tsv']}]




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
      <th>run</th>
      <th>file_count</th>
      <th>subjects</th>
      <th>_file_paths</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>nback</td>
      <td>01</td>
      <td>10</td>
      <td>5</td>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/fun...</td>
    </tr>
    <tr>
      <th>1</th>
      <td>nback</td>
      <td>02</td>
      <td>10</td>
      <td>5</td>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/fun...</td>
    </tr>
    <tr>
      <th>2</th>
      <td>rest</td>
      <td>None</td>
      <td>10</td>
      <td>5</td>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/fun...</td>
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
      <th>_file_paths</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>01</td>
      <td>12</td>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/ana...</td>
    </tr>
    <tr>
      <th>1</th>
      <td>04</td>
      <td>12</td>
      <td>/tmp/bids-examples/synthetic/sub-04/ses-02/ana...</td>
    </tr>
    <tr>
      <th>2</th>
      <td>05</td>
      <td>12</td>
      <td>/tmp/bids-examples/synthetic/sub-05/ses-02/ana...</td>
    </tr>
    <tr>
      <th>3</th>
      <td>02</td>
      <td>12</td>
      <td>/tmp/bids-examples/synthetic/sub-02/ses-02/ana...</td>
    </tr>
    <tr>
      <th>4</th>
      <td>03</td>
      <td>12</td>
      <td>/tmp/bids-examples/synthetic/sub-03/ses-02/ana...</td>
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




    [{'sub': '01',
      'datatype': 'anat',
      'count': 2,
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-01/ses-02/anat/sub-01_ses-02_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-01/anat/sub-01_ses-01_T1w.nii']},
     {'sub': '01',
      'datatype': 'func',
      'count': 6,
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-01/ses-02/func/sub-01_ses-02_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-02/func/sub-01_ses-02_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-02/func/sub-01_ses-02_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-01/func/sub-01_ses-01_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-01/func/sub-01_ses-01_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-01/func/sub-01_ses-01_task-nback_run-01_bold.nii']},
     {'sub': '04',
      'datatype': 'anat',
      'count': 2,
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-04/ses-02/anat/sub-04_ses-02_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-01/anat/sub-04_ses-01_T1w.nii']},
     {'sub': '04',
      'datatype': 'func',
      'count': 6,
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-04/ses-02/func/sub-04_ses-02_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-02/func/sub-04_ses-02_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-02/func/sub-04_ses-02_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-01/func/sub-04_ses-01_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-01/func/sub-04_ses-01_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-01/func/sub-04_ses-01_task-nback_run-01_bold.nii']},
     {'sub': '05',
      'datatype': 'anat',
      'count': 2,
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-05/ses-02/anat/sub-05_ses-02_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-01/anat/sub-05_ses-01_T1w.nii']},
     {'sub': '05',
      'datatype': 'func',
      'count': 6,
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-05/ses-02/func/sub-05_ses-02_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-02/func/sub-05_ses-02_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-02/func/sub-05_ses-02_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-01/func/sub-05_ses-01_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-01/func/sub-05_ses-01_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-01/func/sub-05_ses-01_task-nback_run-01_bold.nii']},
     {'sub': '02',
      'datatype': 'anat',
      'count': 2,
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-02/ses-02/anat/sub-02_ses-02_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-01/anat/sub-02_ses-01_T1w.nii']},
     {'sub': '02',
      'datatype': 'func',
      'count': 6,
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-02/ses-02/func/sub-02_ses-02_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-02/func/sub-02_ses-02_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-02/func/sub-02_ses-02_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-01/func/sub-02_ses-01_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-01/func/sub-02_ses-01_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-01/func/sub-02_ses-01_task-rest_bold.nii']},
     {'sub': '03',
      'datatype': 'anat',
      'count': 2,
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-03/ses-02/anat/sub-03_ses-02_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-01/anat/sub-03_ses-01_T1w.nii']},
     {'sub': '03',
      'datatype': 'func',
      'count': 6,
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-03/ses-02/func/sub-03_ses-02_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-02/func/sub-03_ses-02_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-02/func/sub-03_ses-02_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-01/func/sub-03_ses-01_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-01/func/sub-03_ses-01_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-01/func/sub-03_ses-01_task-nback_run-01_bold.nii']},
     {'sub': '01',
      'datatype': None,
      'count': 3,
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-01/sub-01_sessions.tsv',
       '/tmp/bids-examples/synthetic/sub-01/ses-02/sub-01_ses-02_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-01/ses-01/sub-01_ses-01_scans.tsv']},
     {'sub': '01',
      'datatype': 'beh',
      'count': 1,
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-01/ses-01/beh/sub-01_ses-01_task-stroop_beh.tsv']},
     {'sub': '04',
      'datatype': None,
      'count': 3,
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-04/sub-04_sessions.tsv',
       '/tmp/bids-examples/synthetic/sub-04/ses-02/sub-04_ses-02_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-04/ses-01/sub-04_ses-01_scans.tsv']},
     {'sub': '04',
      'datatype': 'beh',
      'count': 1,
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-04/ses-01/beh/sub-04_ses-01_task-stroop_beh.tsv']},
     {'sub': '05',
      'datatype': None,
      'count': 3,
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-05/sub-05_sessions.tsv',
       '/tmp/bids-examples/synthetic/sub-05/ses-02/sub-05_ses-02_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-05/ses-01/sub-05_ses-01_scans.tsv']},
     {'sub': '05',
      'datatype': 'beh',
      'count': 1,
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-05/ses-01/beh/sub-05_ses-01_task-stroop_beh.tsv']},
     {'sub': '02',
      'datatype': None,
      'count': 3,
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-02/sub-02_sessions.tsv',
       '/tmp/bids-examples/synthetic/sub-02/ses-02/sub-02_ses-02_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-02/ses-01/sub-02_ses-01_scans.tsv']},
     {'sub': '02',
      'datatype': 'beh',
      'count': 1,
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-02/ses-01/beh/sub-02_ses-01_task-stroop_beh.tsv']},
     {'sub': '03',
      'datatype': None,
      'count': 3,
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-03/sub-03_sessions.tsv',
       '/tmp/bids-examples/synthetic/sub-03/ses-02/sub-03_ses-02_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-03/ses-01/sub-03_ses-01_scans.tsv']},
     {'sub': '03',
      'datatype': 'beh',
      'count': 1,
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-03/ses-01/beh/sub-03_ses-01_task-stroop_beh.tsv']}]



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




    [{'task': None,
      'file_count': 25,
      'subjects_with_task': ['01', '02', '03', '04', '05'],
      'datatypes': ['anat'],
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-01/ses-02/anat/sub-01_ses-02_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-01/anat/sub-01_ses-01_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-02/anat/sub-04_ses-02_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-01/anat/sub-04_ses-01_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-02/anat/sub-05_ses-02_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-01/anat/sub-05_ses-01_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-02/anat/sub-02_ses-02_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-01/anat/sub-02_ses-01_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-02/anat/sub-03_ses-02_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-01/anat/sub-03_ses-01_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-01/sub-01_sessions.tsv',
       '/tmp/bids-examples/synthetic/sub-01/ses-02/sub-01_ses-02_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-01/ses-01/sub-01_ses-01_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-04/sub-04_sessions.tsv',
       '/tmp/bids-examples/synthetic/sub-04/ses-02/sub-04_ses-02_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-04/ses-01/sub-04_ses-01_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-05/sub-05_sessions.tsv',
       '/tmp/bids-examples/synthetic/sub-05/ses-02/sub-05_ses-02_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-05/ses-01/sub-05_ses-01_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-02/sub-02_sessions.tsv',
       '/tmp/bids-examples/synthetic/sub-02/ses-02/sub-02_ses-02_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-02/ses-01/sub-02_ses-01_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-03/sub-03_sessions.tsv',
       '/tmp/bids-examples/synthetic/sub-03/ses-02/sub-03_ses-02_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-03/ses-01/sub-03_ses-01_scans.tsv']},
     {'task': 'nback',
      'file_count': 20,
      'subjects_with_task': ['01', '02', '03', '04', '05'],
      'datatypes': ['func'],
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-01/ses-02/func/sub-01_ses-02_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-02/func/sub-01_ses-02_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-01/func/sub-01_ses-01_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-01/func/sub-01_ses-01_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-02/func/sub-04_ses-02_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-02/func/sub-04_ses-02_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-01/func/sub-04_ses-01_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-01/func/sub-04_ses-01_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-02/func/sub-05_ses-02_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-02/func/sub-05_ses-02_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-01/func/sub-05_ses-01_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-01/func/sub-05_ses-01_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-02/func/sub-02_ses-02_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-02/func/sub-02_ses-02_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-01/func/sub-02_ses-01_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-01/func/sub-02_ses-01_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-02/func/sub-03_ses-02_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-02/func/sub-03_ses-02_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-01/func/sub-03_ses-01_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-01/func/sub-03_ses-01_task-nback_run-01_bold.nii']},
     {'task': 'rest',
      'file_count': 10,
      'subjects_with_task': ['01', '02', '03', '04', '05'],
      'datatypes': ['func'],
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-01/ses-02/func/sub-01_ses-02_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-01/func/sub-01_ses-01_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-02/func/sub-04_ses-02_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-01/func/sub-04_ses-01_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-02/func/sub-05_ses-02_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-01/func/sub-05_ses-01_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-02/func/sub-02_ses-02_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-01/func/sub-02_ses-01_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-02/func/sub-03_ses-02_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-01/func/sub-03_ses-01_task-rest_bold.nii']},
     {'task': 'stroop',
      'file_count': 5,
      'subjects_with_task': ['01', '02', '03', '04', '05'],
      'datatypes': ['beh'],
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-01/ses-01/beh/sub-01_ses-01_task-stroop_beh.tsv',
       '/tmp/bids-examples/synthetic/sub-04/ses-01/beh/sub-04_ses-01_task-stroop_beh.tsv',
       '/tmp/bids-examples/synthetic/sub-05/ses-01/beh/sub-05_ses-01_task-stroop_beh.tsv',
       '/tmp/bids-examples/synthetic/sub-02/ses-01/beh/sub-02_ses-01_task-stroop_beh.tsv',
       '/tmp/bids-examples/synthetic/sub-03/ses-01/beh/sub-03_ses-01_task-stroop_beh.tsv']}]




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




    [{'datatype': 'anat',
      'total_files': 10,
      'subjects': 5,
      'subject_list': ['01', '02', '03', '04', '05'],
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-01/ses-02/anat/sub-01_ses-02_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-01/anat/sub-01_ses-01_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-02/anat/sub-04_ses-02_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-01/anat/sub-04_ses-01_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-02/anat/sub-05_ses-02_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-01/anat/sub-05_ses-01_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-02/anat/sub-02_ses-02_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-01/anat/sub-02_ses-01_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-02/anat/sub-03_ses-02_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-01/anat/sub-03_ses-01_T1w.nii']},
     {'datatype': 'func',
      'total_files': 30,
      'subjects': 5,
      'subject_list': ['01', '02', '03', '04', '05'],
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-01/ses-02/func/sub-01_ses-02_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-02/func/sub-01_ses-02_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-02/func/sub-01_ses-02_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-01/func/sub-01_ses-01_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-01/func/sub-01_ses-01_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-01/func/sub-01_ses-01_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-02/func/sub-04_ses-02_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-02/func/sub-04_ses-02_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-02/func/sub-04_ses-02_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-01/func/sub-04_ses-01_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-01/func/sub-04_ses-01_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-01/func/sub-04_ses-01_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-02/func/sub-05_ses-02_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-02/func/sub-05_ses-02_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-02/func/sub-05_ses-02_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-01/func/sub-05_ses-01_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-01/func/sub-05_ses-01_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-01/func/sub-05_ses-01_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-02/func/sub-02_ses-02_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-02/func/sub-02_ses-02_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-02/func/sub-02_ses-02_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-01/func/sub-02_ses-01_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-01/func/sub-02_ses-01_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-01/func/sub-02_ses-01_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-02/func/sub-03_ses-02_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-02/func/sub-03_ses-02_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-02/func/sub-03_ses-02_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-01/func/sub-03_ses-01_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-01/func/sub-03_ses-01_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-01/func/sub-03_ses-01_task-nback_run-01_bold.nii']},
     {'datatype': None,
      'total_files': 15,
      'subjects': 5,
      'subject_list': ['01', '02', '03', '04', '05'],
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-01/sub-01_sessions.tsv',
       '/tmp/bids-examples/synthetic/sub-01/ses-02/sub-01_ses-02_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-01/ses-01/sub-01_ses-01_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-04/sub-04_sessions.tsv',
       '/tmp/bids-examples/synthetic/sub-04/ses-02/sub-04_ses-02_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-04/ses-01/sub-04_ses-01_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-05/sub-05_sessions.tsv',
       '/tmp/bids-examples/synthetic/sub-05/ses-02/sub-05_ses-02_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-05/ses-01/sub-05_ses-01_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-02/sub-02_sessions.tsv',
       '/tmp/bids-examples/synthetic/sub-02/ses-02/sub-02_ses-02_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-02/ses-01/sub-02_ses-01_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-03/sub-03_sessions.tsv',
       '/tmp/bids-examples/synthetic/sub-03/ses-02/sub-03_ses-02_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-03/ses-01/sub-03_ses-01_scans.tsv']},
     {'datatype': 'beh',
      'total_files': 5,
      'subjects': 5,
      'subject_list': ['01', '02', '03', '04', '05'],
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-01/ses-01/beh/sub-01_ses-01_task-stroop_beh.tsv',
       '/tmp/bids-examples/synthetic/sub-04/ses-01/beh/sub-04_ses-01_task-stroop_beh.tsv',
       '/tmp/bids-examples/synthetic/sub-05/ses-01/beh/sub-05_ses-01_task-stroop_beh.tsv',
       '/tmp/bids-examples/synthetic/sub-02/ses-01/beh/sub-02_ses-01_task-stroop_beh.tsv',
       '/tmp/bids-examples/synthetic/sub-03/ses-01/beh/sub-03_ses-01_task-stroop_beh.tsv']}]



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
      <th>_file_paths</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>01</td>
      <td>34</td>
      <td>F</td>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/ana...</td>
    </tr>
    <tr>
      <th>1</th>
      <td>04</td>
      <td>21</td>
      <td>F</td>
      <td>/tmp/bids-examples/synthetic/sub-04/ses-02/ana...</td>
    </tr>
    <tr>
      <th>2</th>
      <td>05</td>
      <td>42</td>
      <td>M</td>
      <td>/tmp/bids-examples/synthetic/sub-05/ses-02/ana...</td>
    </tr>
    <tr>
      <th>3</th>
      <td>02</td>
      <td>38</td>
      <td>M</td>
      <td>/tmp/bids-examples/synthetic/sub-02/ses-02/ana...</td>
    </tr>
    <tr>
      <th>4</th>
      <td>03</td>
      <td>22</td>
      <td>M</td>
      <td>/tmp/bids-examples/synthetic/sub-03/ses-02/ana...</td>
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
      <th>_file_paths</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>01</td>
      <td>None</td>
      <td>34</td>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/ana...</td>
    </tr>
    <tr>
      <th>1</th>
      <td>01</td>
      <td>nback</td>
      <td>34</td>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/fun...</td>
    </tr>
    <tr>
      <th>2</th>
      <td>01</td>
      <td>nback</td>
      <td>34</td>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/fun...</td>
    </tr>
    <tr>
      <th>3</th>
      <td>01</td>
      <td>rest</td>
      <td>34</td>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/fun...</td>
    </tr>
    <tr>
      <th>4</th>
      <td>01</td>
      <td>None</td>
      <td>34</td>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-01/ana...</td>
    </tr>
    <tr>
      <th>5</th>
      <td>01</td>
      <td>nback</td>
      <td>34</td>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-01/fun...</td>
    </tr>
    <tr>
      <th>6</th>
      <td>01</td>
      <td>rest</td>
      <td>34</td>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-01/fun...</td>
    </tr>
    <tr>
      <th>7</th>
      <td>01</td>
      <td>nback</td>
      <td>34</td>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-01/fun...</td>
    </tr>
    <tr>
      <th>8</th>
      <td>05</td>
      <td>None</td>
      <td>42</td>
      <td>/tmp/bids-examples/synthetic/sub-05/ses-02/ana...</td>
    </tr>
    <tr>
      <th>9</th>
      <td>05</td>
      <td>rest</td>
      <td>42</td>
      <td>/tmp/bids-examples/synthetic/sub-05/ses-02/fun...</td>
    </tr>
    <tr>
      <th>10</th>
      <td>05</td>
      <td>nback</td>
      <td>42</td>
      <td>/tmp/bids-examples/synthetic/sub-05/ses-02/fun...</td>
    </tr>
    <tr>
      <th>11</th>
      <td>05</td>
      <td>nback</td>
      <td>42</td>
      <td>/tmp/bids-examples/synthetic/sub-05/ses-02/fun...</td>
    </tr>
    <tr>
      <th>12</th>
      <td>05</td>
      <td>None</td>
      <td>42</td>
      <td>/tmp/bids-examples/synthetic/sub-05/ses-01/ana...</td>
    </tr>
    <tr>
      <th>13</th>
      <td>05</td>
      <td>nback</td>
      <td>42</td>
      <td>/tmp/bids-examples/synthetic/sub-05/ses-01/fun...</td>
    </tr>
    <tr>
      <th>14</th>
      <td>05</td>
      <td>rest</td>
      <td>42</td>
      <td>/tmp/bids-examples/synthetic/sub-05/ses-01/fun...</td>
    </tr>
    <tr>
      <th>15</th>
      <td>05</td>
      <td>nback</td>
      <td>42</td>
      <td>/tmp/bids-examples/synthetic/sub-05/ses-01/fun...</td>
    </tr>
    <tr>
      <th>16</th>
      <td>02</td>
      <td>None</td>
      <td>38</td>
      <td>/tmp/bids-examples/synthetic/sub-02/ses-02/ana...</td>
    </tr>
    <tr>
      <th>17</th>
      <td>02</td>
      <td>rest</td>
      <td>38</td>
      <td>/tmp/bids-examples/synthetic/sub-02/ses-02/fun...</td>
    </tr>
    <tr>
      <th>18</th>
      <td>02</td>
      <td>nback</td>
      <td>38</td>
      <td>/tmp/bids-examples/synthetic/sub-02/ses-02/fun...</td>
    </tr>
    <tr>
      <th>19</th>
      <td>02</td>
      <td>nback</td>
      <td>38</td>
      <td>/tmp/bids-examples/synthetic/sub-02/ses-02/fun...</td>
    </tr>
    <tr>
      <th>20</th>
      <td>02</td>
      <td>None</td>
      <td>38</td>
      <td>/tmp/bids-examples/synthetic/sub-02/ses-01/ana...</td>
    </tr>
    <tr>
      <th>21</th>
      <td>02</td>
      <td>nback</td>
      <td>38</td>
      <td>/tmp/bids-examples/synthetic/sub-02/ses-01/fun...</td>
    </tr>
    <tr>
      <th>22</th>
      <td>02</td>
      <td>nback</td>
      <td>38</td>
      <td>/tmp/bids-examples/synthetic/sub-02/ses-01/fun...</td>
    </tr>
    <tr>
      <th>23</th>
      <td>02</td>
      <td>rest</td>
      <td>38</td>
      <td>/tmp/bids-examples/synthetic/sub-02/ses-01/fun...</td>
    </tr>
    <tr>
      <th>24</th>
      <td>01</td>
      <td>None</td>
      <td>34</td>
      <td>/tmp/bids-examples/synthetic/sub-01/sub-01_ses...</td>
    </tr>
    <tr>
      <th>25</th>
      <td>01</td>
      <td>None</td>
      <td>34</td>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/sub...</td>
    </tr>
    <tr>
      <th>26</th>
      <td>01</td>
      <td>None</td>
      <td>34</td>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-01/sub...</td>
    </tr>
    <tr>
      <th>27</th>
      <td>01</td>
      <td>stroop</td>
      <td>34</td>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-01/beh...</td>
    </tr>
    <tr>
      <th>28</th>
      <td>05</td>
      <td>None</td>
      <td>42</td>
      <td>/tmp/bids-examples/synthetic/sub-05/sub-05_ses...</td>
    </tr>
    <tr>
      <th>29</th>
      <td>05</td>
      <td>None</td>
      <td>42</td>
      <td>/tmp/bids-examples/synthetic/sub-05/ses-02/sub...</td>
    </tr>
    <tr>
      <th>30</th>
      <td>05</td>
      <td>None</td>
      <td>42</td>
      <td>/tmp/bids-examples/synthetic/sub-05/ses-01/sub...</td>
    </tr>
    <tr>
      <th>31</th>
      <td>05</td>
      <td>stroop</td>
      <td>42</td>
      <td>/tmp/bids-examples/synthetic/sub-05/ses-01/beh...</td>
    </tr>
    <tr>
      <th>32</th>
      <td>02</td>
      <td>None</td>
      <td>38</td>
      <td>/tmp/bids-examples/synthetic/sub-02/sub-02_ses...</td>
    </tr>
    <tr>
      <th>33</th>
      <td>02</td>
      <td>None</td>
      <td>38</td>
      <td>/tmp/bids-examples/synthetic/sub-02/ses-02/sub...</td>
    </tr>
    <tr>
      <th>34</th>
      <td>02</td>
      <td>None</td>
      <td>38</td>
      <td>/tmp/bids-examples/synthetic/sub-02/ses-01/sub...</td>
    </tr>
    <tr>
      <th>35</th>
      <td>02</td>
      <td>stroop</td>
      <td>38</td>
      <td>/tmp/bids-examples/synthetic/sub-02/ses-01/beh...</td>
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




    [{'sub': '01',
      'ses': '02',
      'task': 'nback',
      'n_runs': 2,
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-01/ses-02/func/sub-01_ses-02_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-02/func/sub-01_ses-02_task-nback_run-01_bold.nii']},
     {'sub': '01',
      'ses': '01',
      'task': 'nback',
      'n_runs': 2,
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-01/ses-01/func/sub-01_ses-01_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-01/func/sub-01_ses-01_task-nback_run-01_bold.nii']},
     {'sub': '02',
      'ses': '02',
      'task': 'nback',
      'n_runs': 2,
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-02/ses-02/func/sub-02_ses-02_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-02/func/sub-02_ses-02_task-nback_run-01_bold.nii']},
     {'sub': '02',
      'ses': '01',
      'task': 'nback',
      'n_runs': 2,
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-02/ses-01/func/sub-02_ses-01_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-01/func/sub-02_ses-01_task-nback_run-01_bold.nii']},
     {'sub': '03',
      'ses': '02',
      'task': 'nback',
      'n_runs': 2,
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-03/ses-02/func/sub-03_ses-02_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-02/func/sub-03_ses-02_task-nback_run-02_bold.nii']},
     {'sub': '03',
      'ses': '01',
      'task': 'nback',
      'n_runs': 2,
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-03/ses-01/func/sub-03_ses-01_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-01/func/sub-03_ses-01_task-nback_run-01_bold.nii']},
     {'sub': '04',
      'ses': '02',
      'task': 'nback',
      'n_runs': 2,
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-04/ses-02/func/sub-04_ses-02_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-02/func/sub-04_ses-02_task-nback_run-01_bold.nii']},
     {'sub': '04',
      'ses': '01',
      'task': 'nback',
      'n_runs': 2,
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-04/ses-01/func/sub-04_ses-01_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-01/func/sub-04_ses-01_task-nback_run-01_bold.nii']},
     {'sub': '05',
      'ses': '02',
      'task': 'nback',
      'n_runs': 2,
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-05/ses-02/func/sub-05_ses-02_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-02/func/sub-05_ses-02_task-nback_run-01_bold.nii']},
     {'sub': '05',
      'ses': '01',
      'task': 'nback',
      'n_runs': 2,
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-05/ses-01/func/sub-05_ses-01_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-01/func/sub-05_ses-01_task-nback_run-01_bold.nii']}]




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




    [{'sub': '01',
      'task': 'nback',
      'run': '02',
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-01/ses-02/func/sub-01_ses-02_task-nback_run-02_bold.nii']},
     {'sub': '01',
      'task': 'nback',
      'run': '01',
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-01/ses-02/func/sub-01_ses-02_task-nback_run-01_bold.nii']}]




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
      <th>_file_paths</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>01</td>
      <td>nback</td>
      <td>02</td>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/fun...</td>
    </tr>
    <tr>
      <th>1</th>
      <td>01</td>
      <td>nback</td>
      <td>01</td>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/fun...</td>
    </tr>
    <tr>
      <th>2</th>
      <td>01</td>
      <td>rest</td>
      <td>None</td>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/fun...</td>
    </tr>
    <tr>
      <th>3</th>
      <td>01</td>
      <td>nback</td>
      <td>02</td>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-01/fun...</td>
    </tr>
    <tr>
      <th>4</th>
      <td>01</td>
      <td>rest</td>
      <td>None</td>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-01/fun...</td>
    </tr>
    <tr>
      <th>5</th>
      <td>01</td>
      <td>nback</td>
      <td>01</td>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-01/fun...</td>
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
           ARRAY_AGG(DISTINCT datatype) as available_data
    GROUP BY sub
""", format="json")
```




    [{'sub': '01',
      'total_files': 12,
      'datatypes': 3,
      'available_data': ['anat', 'beh', 'func'],
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-01/ses-02/anat/sub-01_ses-02_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-02/func/sub-01_ses-02_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-02/func/sub-01_ses-02_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-02/func/sub-01_ses-02_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-01/anat/sub-01_ses-01_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-01/func/sub-01_ses-01_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-01/func/sub-01_ses-01_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-01/func/sub-01_ses-01_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/sub-01_sessions.tsv',
       '/tmp/bids-examples/synthetic/sub-01/ses-02/sub-01_ses-02_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-01/ses-01/sub-01_ses-01_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-01/ses-01/beh/sub-01_ses-01_task-stroop_beh.tsv']},
     {'sub': '04',
      'total_files': 12,
      'datatypes': 3,
      'available_data': ['anat', 'beh', 'func'],
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-04/ses-02/anat/sub-04_ses-02_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-02/func/sub-04_ses-02_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-02/func/sub-04_ses-02_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-02/func/sub-04_ses-02_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-01/anat/sub-04_ses-01_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-01/func/sub-04_ses-01_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-01/func/sub-04_ses-01_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-01/func/sub-04_ses-01_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-04/sub-04_sessions.tsv',
       '/tmp/bids-examples/synthetic/sub-04/ses-02/sub-04_ses-02_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-04/ses-01/sub-04_ses-01_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-04/ses-01/beh/sub-04_ses-01_task-stroop_beh.tsv']},
     {'sub': '05',
      'total_files': 12,
      'datatypes': 3,
      'available_data': ['anat', 'beh', 'func'],
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-05/ses-02/anat/sub-05_ses-02_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-02/func/sub-05_ses-02_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-02/func/sub-05_ses-02_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-02/func/sub-05_ses-02_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-01/anat/sub-05_ses-01_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-01/func/sub-05_ses-01_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-01/func/sub-05_ses-01_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-01/func/sub-05_ses-01_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-05/sub-05_sessions.tsv',
       '/tmp/bids-examples/synthetic/sub-05/ses-02/sub-05_ses-02_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-05/ses-01/sub-05_ses-01_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-05/ses-01/beh/sub-05_ses-01_task-stroop_beh.tsv']},
     {'sub': '02',
      'total_files': 12,
      'datatypes': 3,
      'available_data': ['anat', 'beh', 'func'],
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-02/ses-02/anat/sub-02_ses-02_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-02/func/sub-02_ses-02_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-02/func/sub-02_ses-02_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-02/func/sub-02_ses-02_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-01/anat/sub-02_ses-01_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-01/func/sub-02_ses-01_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-01/func/sub-02_ses-01_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-01/func/sub-02_ses-01_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/sub-02_sessions.tsv',
       '/tmp/bids-examples/synthetic/sub-02/ses-02/sub-02_ses-02_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-02/ses-01/sub-02_ses-01_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-02/ses-01/beh/sub-02_ses-01_task-stroop_beh.tsv']},
     {'sub': '03',
      'total_files': 12,
      'datatypes': 3,
      'available_data': ['anat', 'beh', 'func'],
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-03/ses-02/anat/sub-03_ses-02_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-02/func/sub-03_ses-02_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-02/func/sub-03_ses-02_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-02/func/sub-03_ses-02_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-01/anat/sub-03_ses-01_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-01/func/sub-03_ses-01_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-01/func/sub-03_ses-01_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-01/func/sub-03_ses-01_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/sub-03_sessions.tsv',
       '/tmp/bids-examples/synthetic/sub-03/ses-02/sub-03_ses-02_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-03/ses-01/sub-03_ses-01_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-03/ses-01/beh/sub-03_ses-01_task-stroop_beh.tsv']}]




```python
q.run_query("""
    SELECT sub, ses,
           COUNT(*) as files_per_session,
           ARRAY_AGG(DISTINCT task) as tasks_in_session
    GROUP BY sub, ses
""", format="json")
```




    [{'sub': '01',
      'ses': '02',
      'files_per_session': 5,
      'tasks_in_session': ['nback', 'rest'],
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-01/ses-02/anat/sub-01_ses-02_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-02/func/sub-01_ses-02_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-02/func/sub-01_ses-02_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-02/func/sub-01_ses-02_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-02/sub-01_ses-02_scans.tsv']},
     {'sub': '01',
      'ses': '01',
      'files_per_session': 6,
      'tasks_in_session': ['nback', 'rest', 'stroop'],
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-01/ses-01/anat/sub-01_ses-01_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-01/func/sub-01_ses-01_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-01/func/sub-01_ses-01_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-01/func/sub-01_ses-01_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-01/sub-01_ses-01_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-01/ses-01/beh/sub-01_ses-01_task-stroop_beh.tsv']},
     {'sub': '04',
      'ses': '02',
      'files_per_session': 5,
      'tasks_in_session': ['nback', 'rest'],
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-04/ses-02/anat/sub-04_ses-02_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-02/func/sub-04_ses-02_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-02/func/sub-04_ses-02_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-02/func/sub-04_ses-02_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-02/sub-04_ses-02_scans.tsv']},
     {'sub': '04',
      'ses': '01',
      'files_per_session': 6,
      'tasks_in_session': ['nback', 'rest', 'stroop'],
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-04/ses-01/anat/sub-04_ses-01_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-01/func/sub-04_ses-01_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-01/func/sub-04_ses-01_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-01/func/sub-04_ses-01_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-01/sub-04_ses-01_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-04/ses-01/beh/sub-04_ses-01_task-stroop_beh.tsv']},
     {'sub': '05',
      'ses': '02',
      'files_per_session': 5,
      'tasks_in_session': ['nback', 'rest'],
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-05/ses-02/anat/sub-05_ses-02_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-02/func/sub-05_ses-02_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-02/func/sub-05_ses-02_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-02/func/sub-05_ses-02_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-02/sub-05_ses-02_scans.tsv']},
     {'sub': '05',
      'ses': '01',
      'files_per_session': 6,
      'tasks_in_session': ['nback', 'rest', 'stroop'],
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-05/ses-01/anat/sub-05_ses-01_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-01/func/sub-05_ses-01_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-01/func/sub-05_ses-01_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-01/func/sub-05_ses-01_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-01/sub-05_ses-01_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-05/ses-01/beh/sub-05_ses-01_task-stroop_beh.tsv']},
     {'sub': '02',
      'ses': '02',
      'files_per_session': 5,
      'tasks_in_session': ['nback', 'rest'],
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-02/ses-02/anat/sub-02_ses-02_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-02/func/sub-02_ses-02_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-02/func/sub-02_ses-02_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-02/func/sub-02_ses-02_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-02/sub-02_ses-02_scans.tsv']},
     {'sub': '02',
      'ses': '01',
      'files_per_session': 6,
      'tasks_in_session': ['nback', 'rest', 'stroop'],
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-02/ses-01/anat/sub-02_ses-01_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-01/func/sub-02_ses-01_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-01/func/sub-02_ses-01_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-01/func/sub-02_ses-01_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-01/sub-02_ses-01_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-02/ses-01/beh/sub-02_ses-01_task-stroop_beh.tsv']},
     {'sub': '03',
      'ses': '02',
      'files_per_session': 5,
      'tasks_in_session': ['nback', 'rest'],
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-03/ses-02/anat/sub-03_ses-02_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-02/func/sub-03_ses-02_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-02/func/sub-03_ses-02_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-02/func/sub-03_ses-02_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-02/sub-03_ses-02_scans.tsv']},
     {'sub': '03',
      'ses': '01',
      'files_per_session': 6,
      'tasks_in_session': ['nback', 'rest', 'stroop'],
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-03/ses-01/anat/sub-03_ses-01_T1w.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-01/func/sub-03_ses-01_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-01/func/sub-03_ses-01_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-01/func/sub-03_ses-01_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-01/sub-03_ses-01_scans.tsv',
       '/tmp/bids-examples/synthetic/sub-03/ses-01/beh/sub-03_ses-01_task-stroop_beh.tsv']},
     {'sub': '01',
      'ses': None,
      'files_per_session': 1,
      'tasks_in_session': [],
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-01/sub-01_sessions.tsv']},
     {'sub': '04',
      'ses': None,
      'files_per_session': 1,
      'tasks_in_session': [],
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-04/sub-04_sessions.tsv']},
     {'sub': '05',
      'ses': None,
      'files_per_session': 1,
      'tasks_in_session': [],
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-05/sub-05_sessions.tsv']},
     {'sub': '02',
      'ses': None,
      'files_per_session': 1,
      'tasks_in_session': [],
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-02/sub-02_sessions.tsv']},
     {'sub': '03',
      'ses': None,
      'files_per_session': 1,
      'tasks_in_session': [],
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-03/sub-03_sessions.tsv']}]




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




    [{'sub': '01',
      'unique_tasks': 2,
      'completed_tasks': ['nback', 'rest'],
      'total_functional_files': 6,
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-01/ses-02/func/sub-01_ses-02_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-02/func/sub-01_ses-02_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-02/func/sub-01_ses-02_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-01/func/sub-01_ses-01_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-01/func/sub-01_ses-01_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-01/ses-01/func/sub-01_ses-01_task-nback_run-01_bold.nii']},
     {'sub': '04',
      'unique_tasks': 2,
      'completed_tasks': ['nback', 'rest'],
      'total_functional_files': 6,
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-04/ses-02/func/sub-04_ses-02_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-02/func/sub-04_ses-02_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-02/func/sub-04_ses-02_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-01/func/sub-04_ses-01_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-01/func/sub-04_ses-01_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-04/ses-01/func/sub-04_ses-01_task-nback_run-01_bold.nii']},
     {'sub': '05',
      'unique_tasks': 2,
      'completed_tasks': ['nback', 'rest'],
      'total_functional_files': 6,
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-05/ses-02/func/sub-05_ses-02_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-02/func/sub-05_ses-02_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-02/func/sub-05_ses-02_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-01/func/sub-05_ses-01_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-01/func/sub-05_ses-01_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-05/ses-01/func/sub-05_ses-01_task-nback_run-01_bold.nii']},
     {'sub': '02',
      'unique_tasks': 2,
      'completed_tasks': ['nback', 'rest'],
      'total_functional_files': 6,
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-02/ses-02/func/sub-02_ses-02_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-02/func/sub-02_ses-02_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-02/func/sub-02_ses-02_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-01/func/sub-02_ses-01_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-01/func/sub-02_ses-01_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-02/ses-01/func/sub-02_ses-01_task-rest_bold.nii']},
     {'sub': '03',
      'unique_tasks': 2,
      'completed_tasks': ['nback', 'rest'],
      'total_functional_files': 6,
      '_file_paths': ['/tmp/bids-examples/synthetic/sub-03/ses-02/func/sub-03_ses-02_task-nback_run-01_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-02/func/sub-03_ses-02_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-02/func/sub-03_ses-02_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-01/func/sub-03_ses-01_task-rest_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-01/func/sub-03_ses-01_task-nback_run-02_bold.nii',
       '/tmp/bids-examples/synthetic/sub-03/ses-01/func/sub-03_ses-01_task-nback_run-01_bold.nii']}]



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
