# BIQL - BIDS Query Language

A powerful query language for Brain Imaging Data Structure (BIDS) datasets that allows you to search, filter, and extract information using SQL-like syntax.

## Features

- **Entity-based queries**: Search by BIDS entities (subject, session, task, run, etc.)
- **Logical operators**: AND, OR, NOT with proper bracketing support
- **Advanced filtering**: Wildcards, regular expressions, range queries
- **Metadata queries**: Access JSON sidecar metadata with dot notation
- **Multiple output formats**: JSON, table, CSV, file paths
- **SQL-like syntax**: SELECT, WHERE, GROUP BY, ORDER BY clauses

## Installation

```bash
pip install biql
```

## Quick Start

```bash
# Find all T1w anatomical files
biql "suffix=T1w"

# Find functional files for specific subjects
biql "subject IN ['01', '02'] AND datatype=func"

# Complex query with metadata filtering
biql "task=rest AND metadata.RepetitionTime<3.0"

# Select specific fields and format as table
biql "SELECT subject, session, filepath WHERE datatype=anat FORMAT table"
```

## Query Language Syntax

### Basic Entity Queries
```sql
subject=01
task=rest
datatype=func
run=[1:5]
```

### Logical Operations
```sql
subject=01 AND task=rest
(subject=01 OR subject=02) AND datatype=func
NOT task=localizer
```

### Wildcards and Patterns
```sql
subject=control*
task=*memory*
suffix~=/T[12]w/
```

### Metadata Queries
```sql
metadata.RepetitionTime<3.0
metadata.EchoTime=[0.01:0.05]
participants.age>18
```

### SELECT Clauses
```sql
SELECT subject, session, filepath WHERE task=rest
SELECT COUNT(*) GROUP BY subject
SELECT DISTINCT datatype
```

## Documentation

For complete documentation, examples, and API reference, visit: [https://biql.readthedocs.io](https://biql.readthedocs.io)

## License

MIT License - see LICENSE file for details.