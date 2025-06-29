"""
Lexer for BIDS Query Language (BIQL)

Tokenizes BIQL query strings into a stream of tokens for parsing.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, List


class TokenType(Enum):
    # Literals
    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()

    # Operators
    EQ = auto()  # =
    NEQ = auto()  # !=
    GT = auto()  # >
    LT = auto()  # <
    GTE = auto()  # >=
    LTE = auto()  # <=
    MATCH = auto()  # ~=

    # Logical
    AND = auto()
    OR = auto()
    NOT = auto()

    # Delimiters
    LPAREN = auto()  # (
    RPAREN = auto()  # )
    LBRACKET = auto()  # [
    RBRACKET = auto()  # ]
    COMMA = auto()  # ,
    DOT = auto()  # .
    COLON = auto()  # :
    SLASH = auto()  # /
    STAR = auto()  # *
    QUESTION = auto()  # ?

    # Keywords
    SELECT = auto()
    WHERE = auto()
    FROM = auto()
    GROUP = auto()
    BY = auto()
    HAVING = auto()
    ORDER = auto()
    ASC = auto()
    DESC = auto()
    FORMAT = auto()
    COUNT = auto()
    AVG = auto()
    MAX = auto()
    MIN = auto()
    SUM = auto()
    ARRAY_AGG = auto()
    DISTINCT = auto()
    AS = auto()
    IN = auto()
    LIKE = auto()

    # Special
    EOF = auto()
    NEWLINE = auto()


@dataclass
class Token:
    type: TokenType
    value: Any
    position: int


class BIQLLexer:
    """Tokenizes BIQL queries"""

    def __init__(self, query: str):
        self.query = query
        self.position = 0
        self.tokens: List[Token] = []

    def tokenize(self) -> List[Token]:
        """Tokenize the query string and return list of tokens"""
        while self.position < len(self.query):
            self._skip_whitespace()
            if self.position >= len(self.query):
                break

            # Comments
            if self._peek() == "#":
                self._skip_comment()
                continue

            # String literals
            if self._peek() in "\"'":
                self._read_string()
            # Numbers
            elif self._peek().isdigit():
                self._read_number()
            # Identifiers and keywords
            elif self._peek().isalpha() or self._peek() == "_":
                self._read_identifier()
            # Operators and delimiters
            else:
                self._read_operator()

        self.tokens.append(Token(TokenType.EOF, None, self.position))
        return self.tokens

    def _peek(self, offset: int = 0) -> str:
        """Peek at character at current position + offset"""
        pos = self.position + offset
        if pos < len(self.query):
            return self.query[pos]
        return ""

    def _advance(self):
        """Advance position by one character"""
        self.position += 1

    def _skip_whitespace(self):
        """Skip whitespace characters"""
        while self.position < len(self.query) and self.query[self.position].isspace():
            self.position += 1

    def _skip_comment(self):
        """Skip comment until end of line"""
        while self.position < len(self.query) and self.query[self.position] != "\n":
            self.position += 1

    def _read_string(self):
        """Read string literal with quote escaping"""
        start_pos = self.position
        quote_char = self.query[self.position]
        self._advance()  # Skip opening quote

        value = ""
        while (
            self.position < len(self.query) and self.query[self.position] != quote_char
        ):
            if self.query[self.position] == "\\":
                self._advance()
                if self.position < len(self.query):
                    value += self.query[self.position]
            else:
                value += self.query[self.position]
            self._advance()

        if self.position < len(self.query):
            self._advance()  # Skip closing quote

        self.tokens.append(Token(TokenType.STRING, value, start_pos))

    def _read_number(self):
        """Read numeric literal (int or float)"""
        start_pos = self.position
        value = ""

        while self.position < len(self.query) and (
            self.query[self.position].isdigit() or self.query[self.position] == "."
        ):
            value += self.query[self.position]
            self._advance()

        if "." in value:
            self.tokens.append(Token(TokenType.NUMBER, float(value), start_pos))
        else:
            self.tokens.append(Token(TokenType.NUMBER, int(value), start_pos))

    def _read_identifier(self):
        """Read identifier or keyword"""
        start_pos = self.position
        value = ""

        while self.position < len(self.query) and (
            self.query[self.position].isalnum() or self.query[self.position] in "_-"
        ):
            value += self.query[self.position]
            self._advance()

        # Check if it's a keyword
        keyword_map = {
            "AND": TokenType.AND,
            "OR": TokenType.OR,
            "NOT": TokenType.NOT,
            "SELECT": TokenType.SELECT,
            "WHERE": TokenType.WHERE,
            "FROM": TokenType.FROM,
            "GROUP": TokenType.GROUP,
            "BY": TokenType.BY,
            "HAVING": TokenType.HAVING,
            "ORDER": TokenType.ORDER,
            "ASC": TokenType.ASC,
            "DESC": TokenType.DESC,
            "FORMAT": TokenType.FORMAT,
            "COUNT": TokenType.COUNT,
            "AVG": TokenType.AVG,
            "MAX": TokenType.MAX,
            "MIN": TokenType.MIN,
            "SUM": TokenType.SUM,
            "ARRAY_AGG": TokenType.ARRAY_AGG,
            "DISTINCT": TokenType.DISTINCT,
            "AS": TokenType.AS,
            "IN": TokenType.IN,
            "LIKE": TokenType.LIKE,
        }

        token_type = keyword_map.get(value.upper(), TokenType.IDENTIFIER)
        if token_type != TokenType.IDENTIFIER:
            value = value.upper()

        self.tokens.append(Token(token_type, value, start_pos))

    def _read_operator(self):
        """Read operators and delimiters"""
        start_pos = self.position
        char = self.query[self.position]

        if char == "=" and self._peek(1) == "=":
            self._advance()
            self._advance()
            self.tokens.append(Token(TokenType.EQ, "==", start_pos))
        elif char == "=":
            self._advance()
            self.tokens.append(Token(TokenType.EQ, "=", start_pos))
        elif char == "!" and self._peek(1) == "=":
            self._advance()
            self._advance()
            self.tokens.append(Token(TokenType.NEQ, "!=", start_pos))
        elif char == ">" and self._peek(1) == "=":
            self._advance()
            self._advance()
            self.tokens.append(Token(TokenType.GTE, ">=", start_pos))
        elif char == ">":
            self._advance()
            self.tokens.append(Token(TokenType.GT, ">", start_pos))
        elif char == "<" and self._peek(1) == "=":
            self._advance()
            self._advance()
            self.tokens.append(Token(TokenType.LTE, "<=", start_pos))
        elif char == "<":
            self._advance()
            self.tokens.append(Token(TokenType.LT, "<", start_pos))
        elif char == "~" and self._peek(1) == "=":
            self._advance()
            self._advance()
            self.tokens.append(Token(TokenType.MATCH, "~=", start_pos))
        elif char == "(":
            self._advance()
            self.tokens.append(Token(TokenType.LPAREN, "(", start_pos))
        elif char == ")":
            self._advance()
            self.tokens.append(Token(TokenType.RPAREN, ")", start_pos))
        elif char == "[":
            self._advance()
            self.tokens.append(Token(TokenType.LBRACKET, "[", start_pos))
        elif char == "]":
            self._advance()
            self.tokens.append(Token(TokenType.RBRACKET, "]", start_pos))
        elif char == ",":
            self._advance()
            self.tokens.append(Token(TokenType.COMMA, ",", start_pos))
        elif char == ".":
            self._advance()
            self.tokens.append(Token(TokenType.DOT, ".", start_pos))
        elif char == ":":
            self._advance()
            self.tokens.append(Token(TokenType.COLON, ":", start_pos))
        elif char == "/":
            self._advance()
            self.tokens.append(Token(TokenType.SLASH, "/", start_pos))
        elif char == "*":
            self._advance()
            self.tokens.append(Token(TokenType.STAR, "*", start_pos))
        elif char == "?":
            self._advance()
            self.tokens.append(Token(TokenType.QUESTION, "?", start_pos))
        else:
            self._advance()  # Skip unknown character
