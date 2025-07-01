---
layout: default
title: Home
nav_order: 1
description: "BIDS Query Language - A powerful SQL-like query language for BIDS neuroimaging datasets"
permalink: /
---

# BIDS Query Language (BIQL)

**A powerful SQL-like query language for BIDS neuroimaging datasets**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-107%20passing-green.svg)](tests/)

---

## What is BIQL?

BIDS Query Language (BIQL) is a domain-specific query language designed for the [Brain Imaging Data Structure (BIDS)](https://bids.neuroimaging.io/). It provides a familiar SQL-like syntax for finding, filtering, and analyzing neuroimaging datasets with unprecedented ease and power.

```sql
-- Find all functional scans from specific subjects
SELECT sub, ses, task, run, filepath
WHERE datatype=func AND sub IN [01, 02, 03]
ORDER BY sub, run

-- Get QSM reconstruction groups with file lists
SELECT filename, sub, ses, acq, COUNT(*) as total_files
WHERE (part=mag OR part=phase) AND suffix=MEGRE
GROUP BY sub, ses, acq
```

## Key Features

🔍 **Intuitive Syntax** - SQL-like queries that feel natural to researchers and developers

📊 **Powerful Aggregation** - GROUP BY with auto-aggregated file lists for reconstruction workflows

🎯 **Smart Pattern Matching** - Wildcard and regex support for flexible file discovery

🧠 **BIDS Native** - Deep understanding of BIDS entities, metadata, and participant data

🔧 **Multiple Output Formats** - JSON, CSV, TSV, table, and paths output

## Quick Example

```bash
# Install BIQL
pip install biql

# Query your BIDS dataset
biql --dataset /path/to/bids "SELECT DISTINCT task WHERE datatype=func"

# Get QSM reconstruction groups
biql "SELECT sub, acq, COUNT(*) WHERE part=mag GROUP BY sub, acq" \
     --format table --dataset /data/qsm_study
```

## Use Cases

- **Dataset Exploration** - Quickly understand what data you have
- **Processing Pipelines** - Generate file lists for batch processing
- **Metadata Analysis** - Query acquisition parameters and demographics
- **Quality Control** - Find missing files or inconsistent naming

## Community

- **GitHub**: [Issues and contributions](https://github.com/user/biql)
- **Discussions**: [Ask questions and share queries](https://github.com/user/biql/discussions)
- **BIDS Community**: [Join the broader BIDS ecosystem](https://bids.neuroimaging.io/)

## License

BIQL is open source software released under the [MIT License](https://opensource.org/licenses/MIT).
