"""
Comprehensive tests for BIDS Query Language (BIQL)

Tests all components of the BIQL implementation using real BIDS examples.
"""

import pytest

from biql.lexer import BIQLLexer, TokenType


class TestBIQLLexer:
    """Test the BIQL lexer functionality"""

    def test_basic_tokenization(self):
        """Test basic token recognition"""
        lexer = BIQLLexer("sub=01 AND task=rest")
        tokens = lexer.tokenize()

        token_types = [t.type for t in tokens if t.type != TokenType.EOF]
        expected = [
            TokenType.IDENTIFIER,
            TokenType.EQ,
            TokenType.NUMBER,
            TokenType.AND,
            TokenType.IDENTIFIER,
            TokenType.EQ,
            TokenType.IDENTIFIER,
        ]
        assert token_types == expected

    def test_string_literals(self):
        """Test string literal tokenization"""
        lexer = BIQLLexer('task="n-back" OR suffix="T1w"')
        tokens = lexer.tokenize()

        string_tokens = [t for t in tokens if t.type == TokenType.STRING]
        assert len(string_tokens) == 2
        assert string_tokens[0].value == "n-back"
        assert string_tokens[1].value == "T1w"

    def test_operators(self):
        """Test operator tokenization"""
        lexer = BIQLLexer("metadata.RepetitionTime>=2.0 AND run<=[1:3]")
        tokens = lexer.tokenize()

        operator_tokens = [
            t for t in tokens if t.type in [TokenType.GTE, TokenType.LTE]
        ]
        assert len(operator_tokens) == 2

    def test_complex_query(self):
        """Test complex query tokenization"""
        query = (
            "SELECT sub, ses, filepath WHERE (task=nback OR task=rest) "
            "AND metadata.RepetitionTime<3.0"
        )
        lexer = BIQLLexer(query)
        tokens = lexer.tokenize()

        assert any(t.type == TokenType.SELECT for t in tokens)
        assert any(t.type == TokenType.WHERE for t in tokens)
        assert any(t.type == TokenType.LPAREN for t in tokens)
        assert any(t.type == TokenType.RPAREN for t in tokens)


if __name__ == "__main__":
    # Run specific test categories
    pytest.main([__file__, "-v", "--tb=short"])
