"""
Abstract Syntax Tree (AST) node definitions for BIQL
"""

from dataclasses import dataclass
from typing import Any, List, Optional, Tuple

from .lexer import TokenType


@dataclass
class ASTNode:
    """Base class for all AST nodes"""

    pass


@dataclass
class SelectClause(ASTNode):
    """SELECT clause with list of items and optional aliases"""

    items: List[Tuple[str, Optional[str]]]  # (expression, alias)
    distinct: bool = False


@dataclass
class WhereClause(ASTNode):
    """WHERE clause with condition expression"""

    condition: "Expression"


@dataclass
class Expression(ASTNode):
    """Base class for all expressions"""

    pass


@dataclass
class BinaryOp(Expression):
    """Binary operation with left operand, operator, and right operand"""

    left: Expression
    operator: TokenType
    right: Expression


@dataclass
class UnaryOp(Expression):
    """Unary operation with operator and operand"""

    operator: TokenType
    operand: Expression


@dataclass
class FieldAccess(Expression):
    """Field access expression (e.g., subject, metadata.RepetitionTime)"""

    field: str
    path: Optional[List[str]] = None


@dataclass
class Literal(Expression):
    """Literal value expression"""

    value: Any


@dataclass
class Range(Expression):
    """Range expression for [start:end] syntax"""

    start: Any
    end: Any


@dataclass
class ListExpression(Expression):
    """List expression for IN clauses"""

    items: List[Expression]


@dataclass
class FunctionCall(Expression):
    """Function call expression (e.g., COUNT(*))"""

    name: str
    args: List[Expression]


@dataclass
class ConditionalAggregateFunction(Expression):
    """Conditional aggregate function (e.g., ARRAY_AGG(field WHERE condition))"""

    name: str
    field: Expression
    condition: Optional[Expression] = None


@dataclass
class ParenthesizedExpression(Expression):
    """Parenthesized expression for implicit aggregation (e.g., (DISTINCT field), (field WHERE condition))"""

    expression: Expression
    distinct: bool = False
    condition: Optional[Expression] = None


@dataclass
class Query(ASTNode):
    """Complete BIQL query with all clauses"""

    select_clause: Optional[SelectClause]
    where_clause: Optional[WhereClause]
    group_by: Optional[List[str]]
    having: Optional[Expression]
    order_by: Optional[List[Tuple[str, str]]]  # (field, direction)
    format: Optional[str]
