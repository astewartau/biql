"""
Comprehensive tests for BIDS Query Language (BIQL)

Tests all components of the BIQL implementation using real BIDS examples.
"""

from pathlib import Path

import pytest

from biql.parser import BIQLParseError, BIQLParser


class TestBIQLParser:
    """Test the BIQL parser functionality"""

    def test_simple_query_parsing(self):
        """Test parsing simple queries"""
        parser = BIQLParser.from_string("sub=01")
        query = parser.parse()

        assert query.where_clause is not None
        assert query.select_clause is None

    def test_select_query_parsing(self):
        """Test parsing SELECT queries"""
        parser = BIQLParser.from_string(
            "SELECT sub, task, filepath WHERE datatype=func"
        )
        query = parser.parse()

        assert query.select_clause is not None
        assert len(query.select_clause.items) == 3
        assert query.where_clause is not None

    def test_complex_where_clause(self):
        """Test parsing complex WHERE clauses"""
        parser = BIQLParser.from_string("(sub=01 OR sub=02) AND task=nback")
        query = parser.parse()

        assert query.where_clause is not None

    def test_group_by_parsing(self):
        """Test parsing GROUP BY clauses"""
        parser = BIQLParser.from_string("SELECT sub, COUNT(*) GROUP BY sub")
        query = parser.parse()

        assert query.group_by is not None
        assert "sub" in query.group_by

    def test_order_by_parsing(self):
        """Test parsing ORDER BY clauses"""
        parser = BIQLParser.from_string("sub=01 ORDER BY run DESC")
        query = parser.parse()

        assert query.order_by is not None
        assert query.order_by[0] == ("run", "DESC")

    def test_format_parsing(self):
        """Test parsing FORMAT clauses"""
        parser = BIQLParser.from_string("sub=01 FORMAT table")
        query = parser.parse()

        assert query.format == "table"

    def test_invalid_syntax(self):
        """Test that invalid syntax raises errors"""
        with pytest.raises(BIQLParseError):
            parser = BIQLParser.from_string("SELECT FROM WHERE")
            parser.parse()

    def test_distinct_parsing(self):
        """Test parsing SELECT DISTINCT queries"""
        parser = BIQLParser.from_string("SELECT DISTINCT sub, task")
        query = parser.parse()

        assert query.select_clause is not None
        assert query.select_clause.distinct is True
        assert len(query.select_clause.items) == 2
        assert query.select_clause.items[0] == ("sub", None)
        assert query.select_clause.items[1] == ("task", None)

    def test_non_distinct_parsing(self):
        """Test that regular SELECT queries have distinct=False"""
        parser = BIQLParser.from_string("SELECT sub, task")
        query = parser.parse()

        assert query.select_clause is not None
        assert query.select_clause.distinct is False

    def test_having_clause_parsing(self):
        """Test parsing HAVING clauses"""
        parser = BIQLParser.from_string(
            "SELECT sub, COUNT(*) GROUP BY sub HAVING COUNT(*) > 2"
        )
        query = parser.parse()

        assert query.group_by is not None
        assert query.having is not None

    def test_function_call_parsing_with_arguments(self):
        """Test parsing function calls with different argument types"""
        # Function with STAR argument
        parser = BIQLParser.from_string("SELECT COUNT(*)")
        query = parser.parse()

        assert query.select_clause is not None
        assert len(query.select_clause.items) == 1
        assert query.select_clause.items[0][0] == "COUNT(*)"

        # Function with field argument
        parser = BIQLParser.from_string("SELECT AVG(metadata.RepetitionTime)")
        query = parser.parse()

        assert query.select_clause is not None
        assert len(query.select_clause.items) == 1
        # Should parse as AVG(metadata.RepetitionTime)
        assert "AVG" in query.select_clause.items[0][0]

    def test_not_operator_parsing(self):
        """Test parsing NOT operator"""
        parser = BIQLParser.from_string("NOT datatype=func")
        query = parser.parse()

        assert query.where_clause is not None
        # Should parse successfully

    def test_complex_function_calls_in_select(self):
        """Test function calls in SELECT with aliases"""
        parser = BIQLParser.from_string("SELECT COUNT(*) AS total_files, sub")
        query = parser.parse()

        assert query.select_clause is not None
        assert len(query.select_clause.items) == 2
        assert query.select_clause.items[0] == ("COUNT(*)", "total_files")
        assert query.select_clause.items[1] == ("sub", None)

    def test_list_expression_parsing(self):
        """Test parsing list expressions in IN clauses"""
        parser = BIQLParser.from_string("sub IN [01, 02, 03]")
        query = parser.parse()

        assert query.where_clause is not None
        # Should parse without errors

    def test_wildcard_pattern_parsing_edge_cases(self):
        """Test wildcard pattern parsing with mixed patterns"""
        # Test identifier followed by wildcard
        parser = BIQLParser.from_string("suffix=bold*")
        query = parser.parse()

        assert query.where_clause is not None

        # Test pattern with question marks
        parser = BIQLParser.from_string("suffix=T?w")
        query = parser.parse()

        assert query.where_clause is not None

    def test_multiple_comma_separated_items(self):
        """Test parsing multiple comma-separated items in various contexts"""
        # Multiple ORDER BY fields
        parser = BIQLParser.from_string("sub=01 ORDER BY sub ASC, ses DESC, run ASC")
        query = parser.parse()

        assert query.order_by is not None
        assert len(query.order_by) == 3
        assert query.order_by[0] == ("sub", "ASC")
        assert query.order_by[1] == ("ses", "DESC")
        assert query.order_by[2] == ("run", "ASC")

        # Multiple GROUP BY fields
        parser = BIQLParser.from_string("SELECT COUNT(*) GROUP BY sub, ses, datatype")
        query = parser.parse()

        assert query.group_by is not None
        assert len(query.group_by) == 3
        assert "sub" in query.group_by
        assert "ses" in query.group_by
        assert "datatype" in query.group_by

    def test_array_agg_parsing(self):
        """Test parsing of ARRAY_AGG functions"""
        # Test basic ARRAY_AGG
        parser = BIQLParser.from_string("SELECT ARRAY_AGG(filename)")
        query = parser.parse()

        assert query.select_clause is not None
        assert len(query.select_clause.items) == 1
        assert query.select_clause.items[0][0] == "ARRAY_AGG(filename)"

        # Test ARRAY_AGG with WHERE condition
        parser = BIQLParser.from_string("SELECT ARRAY_AGG(filename WHERE part='mag')")
        query = parser.parse()

        assert query.select_clause is not None
        assert len(query.select_clause.items) == 1
        assert (
            "ARRAY_AGG(filename WHERE part = 'mag')" in query.select_clause.items[0][0]
        )

        # Test ARRAY_AGG with alias
        parser = BIQLParser.from_string(
            "SELECT ARRAY_AGG(filename WHERE part='phase') AS phase_files"
        )
        query = parser.parse()

        assert query.select_clause is not None
        assert len(query.select_clause.items) == 1
        assert query.select_clause.items[0][1] == "phase_files"

        # Test multiple ARRAY_AGG functions
        parser = BIQLParser.from_string(
            "SELECT ARRAY_AGG(filename WHERE part='mag') AS mag_files, "
            "ARRAY_AGG(filename WHERE part='phase') AS phase_files"
        )
        query = parser.parse()

        assert query.select_clause is not None
        assert len(query.select_clause.items) == 2
        assert query.select_clause.items[0][1] == "mag_files"
        assert query.select_clause.items[1][1] == "phase_files"


if __name__ == "__main__":
    # Run specific test categories
    pytest.main([__file__, "-v", "--tb=short"])
