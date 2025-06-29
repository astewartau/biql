# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-06-28

### Added
- Initial release of BIDS Query Language (BIQL)
- Complete lexer and parser for BIQL syntax
- BIDS dataset indexing and file parsing
- Query evaluator with support for:
  - Entity-based queries (subject, session, task, run, etc.)
  - Logical operators (AND, OR, NOT) with proper precedence
  - Comparison operators (=, !=, >, <, >=, <=, ~=)
  - Wildcard and regular expression pattern matching
  - Range queries ([start:end])
  - Metadata queries (metadata.field)
  - Participant data queries (participants.field)
  - SELECT clauses with field selection and aliases
  - GROUP BY aggregation
  - ORDER BY sorting
  - FORMAT output specification
- Command-line interface (CLI) with comprehensive options
- Multiple output formats: JSON, table, CSV, TSV, paths
- Comprehensive test suite with real BIDS dataset examples
- Performance tests for scalability
- Documentation and examples
- Support for BIDS metadata inheritance
- Support for participants.tsv integration

### Features
- **Query Language**: SQL-like syntax for BIDS datasets
- **Entity Support**: All standard BIDS entities (sub, ses, task, run, etc.)
- **Pattern Matching**: Wildcards (*,?) and regex (/pattern/) support
- **Metadata Access**: Query JSON sidecar metadata with dot notation
- **Participant Data**: Access participants.tsv data in queries
- **Flexible Output**: Multiple output formats for different use cases
- **Performance**: Optimized for large datasets with thousands of files
- **CLI Tools**: Command-line interface with extensive options
- **Validation**: Query syntax validation without execution
- **Debug Mode**: Detailed debugging information for troubleshooting

### Supported Query Examples
```sql
-- Basic entity queries
sub=01
datatype=func AND task=rest

-- Pattern matching
sub=control* OR task~=/.*memory.*/

-- Metadata queries
metadata.RepetitionTime<3.0 AND metadata.EchoTime>[0.01:0.05]

-- Participant queries
participants.age>18 AND participants.sex="F"

-- SELECT with aggregation
SELECT sub, COUNT(*) GROUP BY sub HAVING COUNT(*)>10

-- Complex queries
SELECT sub, ses, task, filepath
WHERE (datatype=func OR datatype=anat) AND sub=[01:05]
ORDER BY sub, task DESC
```

### Installation
```bash
pip install biql
```

### CLI Usage
```bash
# Basic queries
biql "sub=01 AND datatype=func"

# Output formats
biql "task=rest" --format table
biql "datatype=anat" --format paths

# Dataset information
biql --show-stats
biql --show-entities
```

### Python API
```python
from biql import BIDSDataset, BIQLEvaluator, BIQLParser

dataset = BIDSDataset("/path/to/bids/dataset")
evaluator = BIQLEvaluator(dataset)
parser = BIQLParser.from_string("sub=01 AND datatype=func")
query = parser.parse()
results = evaluator.evaluate(query)
```
