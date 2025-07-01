"""
Query Evaluator for BIDS Query Language (BIQL)

Evaluates parsed BIQL queries against BIDS datasets.
"""

import fnmatch
import re
from collections import defaultdict
from typing import Any, Dict, List

from .ast_nodes import *
from .dataset import BIDSDataset, BIDSFile
from .lexer import TokenType


class BIQLEvaluationError(Exception):
    """Exception raised for BIQL evaluation errors"""

    pass


class BIQLEvaluator:
    """Evaluates BIQL queries against BIDS datasets"""

    def __init__(self, dataset: BIDSDataset):
        self.dataset = dataset
        self._original_matching_files = []

    def evaluate(self, query: Query) -> List[Dict[str, Any]]:
        """Evaluate a query and return results"""
        # Start with all files
        results = self.dataset.files

        # Apply WHERE clause
        if query.where_clause:
            results = [
                f
                for f in results
                if self._evaluate_expression(f, query.where_clause.condition)
            ]

        # Store the original matching files for paths formatter
        self._original_matching_files = results

        # Convert to dictionaries for further processing
        result_dicts = []
        for file in results:
            result_dict = self._file_to_dict(file)
            result_dicts.append(result_dict)

        # Apply GROUP BY or create implicit group for aggregate functions
        if query.group_by:
            result_dicts = self._apply_group_by(result_dicts, query.group_by)
        elif self._has_aggregate_functions(query.select_clause):
            # If SELECT has aggregate functions but no GROUP BY, create single group
            if result_dicts:
                single_group = {
                    "_count": len(result_dicts),
                    "_group": result_dicts,
                    "_aggregates": self._compute_aggregates(result_dicts),
                }
                result_dicts = [single_group]
            else:
                result_dicts = []

        # Apply HAVING
        if query.having:
            # Filter grouped results based on HAVING condition
            result_dicts = [
                r for r in result_dicts if self._evaluate_having(r, query.having)
            ]

        # Apply ORDER BY
        if query.order_by:
            for field, direction in reversed(query.order_by):
                reverse = direction == "DESC"
                result_dicts.sort(
                    key=lambda x: self._get_sort_key(x, field), reverse=reverse
                )

        # Apply SELECT
        if query.select_clause:
            result_dicts = self._apply_select(result_dicts, query.select_clause)

            # Apply DISTINCT if specified
            if query.select_clause.distinct:
                result_dicts = self._apply_distinct(result_dicts)

        return result_dicts

    def get_original_matching_files(self) -> List[BIDSFile]:
        """Get the original files that matched the WHERE clause (for paths formatter)"""
        return self._original_matching_files

    def _file_to_dict(self, file: BIDSFile) -> Dict[str, Any]:
        """Convert BIDSFile to dictionary representation"""
        result_dict = {
            "filepath": str(file.filepath),
            "relative_path": str(file.relative_path),
            "filename": file.filepath.name,
            **file.entities,
            "metadata": file.metadata,
        }

        # Add participant data if available
        if "sub" in file.entities and file.entities["sub"] in self.dataset.participants:
            result_dict["participants"] = self.dataset.participants[
                file.entities["sub"]
            ]

        return result_dict

    def _evaluate_expression(self, file: BIDSFile, expr: Expression) -> bool:
        """Evaluate an expression against a file"""
        if isinstance(expr, BinaryOp):
            if expr.operator == TokenType.AND:
                return self._evaluate_expression(
                    file, expr.left
                ) and self._evaluate_expression(file, expr.right)
            elif expr.operator == TokenType.OR:
                return self._evaluate_expression(
                    file, expr.left
                ) or self._evaluate_expression(file, expr.right)
            else:
                # Comparison operators
                left_val = self._get_value(file, expr.left)
                # For comparison right side, handle FieldAccess as literal values
                if isinstance(expr.right, FieldAccess) and expr.right.path is None:
                    # Bare identifier on right side should be treated as literal
                    right_val = expr.right.field
                else:
                    right_val = self._get_value(file, expr.right)
                return self._compare(left_val, expr.operator, right_val)

        elif isinstance(expr, UnaryOp):
            if expr.operator == TokenType.NOT:
                return not self._evaluate_expression(file, expr.operand)

        elif isinstance(expr, FieldAccess):
            # Simple field existence check
            return self._get_value(file, expr) is not None

        return False

    def _get_value(self, file: BIDSFile, expr: Expression) -> Any:
        """Get value from file based on expression"""
        if isinstance(expr, FieldAccess):
            if expr.path:
                # Metadata or participants access
                if expr.field == "metadata" and expr.path:
                    value = file.metadata
                    for part in expr.path:
                        if isinstance(value, dict) and part in value:
                            value = value[part]
                        else:
                            return None
                    return value
                elif expr.field == "participants" and expr.path:
                    if (
                        "sub" in file.entities
                        and file.entities["sub"] in self.dataset.participants
                    ):
                        value = self.dataset.participants[file.entities["sub"]]
                        for part in expr.path:
                            if isinstance(value, dict):
                                # Debug: print what we're looking for vs what's available
                                # print(f"DEBUG: Looking for '{part}' in {list(value.keys())}")
                                # Try exact case first, then lowercase for keywords that got uppercased
                                if part in value:
                                    value = value[part]
                                elif part.lower() in value:
                                    value = value[part.lower()]
                                else:
                                    return None
                            else:
                                return None
                        return value
                    return None
            else:
                # Handle computed fields first
                if expr.field == "filename":
                    return file.filepath.name
                elif expr.field == "filepath":
                    return str(file.filepath)
                elif expr.field == "relative_path":
                    return str(file.relative_path)
                else:
                    # Entity access - return the value from file entities
                    return file.entities.get(expr.field)

        elif isinstance(expr, Literal):
            return expr.value

        elif isinstance(expr, Range):
            # Extract the actual values from the Range expressions
            start_val = self._get_value(file, expr.start)
            end_val = self._get_value(file, expr.end)
            return (start_val, end_val)

        elif isinstance(expr, ListExpression):
            return [self._get_literal_value(item) for item in expr.items]

        return None

    def _get_literal_value(self, expr: Expression) -> Any:
        """Get literal value from expression"""
        if isinstance(expr, Literal):
            return expr.value
        elif isinstance(expr, FieldAccess):
            return expr.field
        return str(expr)

    def _compare(self, left: Any, operator: TokenType, right: Any) -> bool:
        """Compare two values based on operator"""
        # Handle None values
        if left is None:
            return operator == TokenType.NEQ and right is not None
        if right is None:
            return operator == TokenType.NEQ and left is not None

        # Convert FieldAccess to string literal when used as comparison value
        if hasattr(right, "field") and hasattr(right, "path") and right.path is None:
            # This is a bare identifier like 'func' in 'datatype=func'
            right = right.field

        # Handle IN operator with lists
        if operator == TokenType.IN and isinstance(right, list):
            left_str = str(left)

            # Enhanced type coercion for IN operator
            for item in right:
                item_str = str(item)

                # Direct string match
                if left_str == item_str:
                    return True

                # Try zero-padded number comparison for subject IDs
                # Convert numbers to zero-padded strings (e.g., 1 -> "01", 2 -> "02")
                if isinstance(item, (int, float)) and item == int(item):
                    padded_item = f"{int(item):02d}"
                    if left_str == padded_item:
                        return True

                # Try reverse: if left is a number and item is a string
                try:
                    if isinstance(item, str) and left_str.isdigit():
                        if int(left_str) == int(item):
                            return True
                        # Also try zero-padded comparison
                        if f"{int(left_str):02d}" == item:
                            return True
                except ValueError:
                    pass

            return False

        # Convert types if needed for numeric comparison
        if isinstance(right, (int, float)) and isinstance(left, str):
            try:
                left = float(left) if "." in left else int(left)
            except ValueError:
                # If conversion fails, fall back to string comparison
                pass

        # Range comparison
        if isinstance(right, tuple) and len(right) == 2:
            try:
                left_num = float(left) if isinstance(left, str) else left
                # Ensure range bounds are numeric
                start_num = float(right[0]) if isinstance(right[0], str) else right[0]
                end_num = float(right[1]) if isinstance(right[1], str) else right[1]
                return start_num <= left_num <= end_num
            except (ValueError, TypeError):
                return False

        # String pattern matching for equality
        if operator == TokenType.EQ and isinstance(right, str):
            if "*" in right or "?" in right:
                return fnmatch.fnmatch(str(left), right)

        # Regular expression matching
        if operator == TokenType.MATCH and isinstance(right, str):
            try:
                # Remove regex delimiters if present
                pattern = right
                if pattern.startswith("/") and pattern.endswith("/"):
                    pattern = pattern[1:-1]
                return bool(re.match(pattern, str(left)))
            except re.error:
                return False

        # LIKE operator (SQL-style pattern matching)
        if operator == TokenType.LIKE and isinstance(right, str):
            # Convert SQL LIKE pattern to fnmatch pattern
            pattern = right.replace("%", "*").replace("_", "?")
            return fnmatch.fnmatch(str(left), pattern)

        # Standard comparisons
        try:
            if operator == TokenType.EQ:
                return left == right
            elif operator == TokenType.NEQ:
                return left != right
            elif operator == TokenType.GT:
                return left > right
            elif operator == TokenType.LT:
                return left < right
            elif operator == TokenType.GTE:
                return left >= right
            elif operator == TokenType.LTE:
                return left <= right
        except TypeError:
            # Fall back to string comparison for incompatible types
            try:
                left_str, right_str = str(left), str(right)
                if operator == TokenType.EQ:
                    return left_str == right_str
                elif operator == TokenType.NEQ:
                    return left_str != right_str
                elif operator == TokenType.GT:
                    return left_str > right_str
                elif operator == TokenType.LT:
                    return left_str < right_str
                elif operator == TokenType.GTE:
                    return left_str >= right_str
                elif operator == TokenType.LTE:
                    return left_str <= right_str
            except (TypeError, ValueError):
                return False

        return False

    def _apply_group_by(
        self, results: List[Dict], group_fields: List[str]
    ) -> List[Dict]:
        """Apply GROUP BY to results"""
        grouped = defaultdict(list)

        for result in results:
            key = tuple(self._get_nested_value(result, field) for field in group_fields)
            grouped[key].append(result)

        # Create aggregated results
        aggregated = []
        for key, group in grouped.items():
            agg_result = {}
            for i, field in enumerate(group_fields):
                agg_result[field] = key[i]
            agg_result["_count"] = len(group)
            agg_result["_group"] = group

            # Pre-compute aggregate values for the group
            agg_result["_aggregates"] = self._compute_aggregates(group)

            aggregated.append(agg_result)

        return aggregated

    def _compute_aggregates(self, group: List[Dict]) -> Dict[str, Dict[str, Any]]:
        """Compute aggregate values for a group of results"""
        aggregates = defaultdict(dict)

        # Collect all numeric fields from the group
        numeric_fields = set()
        for item in group:
            for key, value in item.items():
                if key not in [
                    "metadata",
                    "participants",
                    "filepath",
                    "relative_path",
                    "filename",
                ]:
                    # Try to convert to number
                    try:
                        float(value) if value is not None else None
                        numeric_fields.add(key)
                    except (ValueError, TypeError):
                        pass

        # Compute aggregates for each numeric field
        for field in numeric_fields:
            values = []
            for item in group:
                value = self._get_nested_value(item, field)
                if value is not None:
                    try:
                        num_value = float(value)
                        values.append(num_value)
                    except (ValueError, TypeError):
                        pass

            if values:
                aggregates[field]["count"] = len(values)
                aggregates[field]["sum"] = sum(values)
                aggregates[field]["avg"] = sum(values) / len(values)
                aggregates[field]["min"] = min(values)
                aggregates[field]["max"] = max(values)

        return dict(aggregates)

    def _has_aggregate_functions(self, select_clause) -> bool:
        """Check if SELECT clause contains aggregate functions"""
        if not select_clause:
            return False

        for item, alias in select_clause.items:
            if item.startswith(("COUNT(", "AVG(", "MAX(", "MIN(", "SUM(", "(")):
                return True
        return False

    def _evaluate_array_agg_condition(self, item: Dict, condition_str: str) -> bool:
        """Evaluate a condition for ARRAY_AGG WHERE clause"""
        try:
            # Import here to avoid circular imports
            from .parser import BIQLParser

            # Parse the condition string as an expression
            parser = BIQLParser.from_string(f"WHERE {condition_str}")
            query = parser.parse()

            if query.where_clause:
                # Evaluate the expression against the item dictionary
                return self._evaluate_expression_dict(
                    item, query.where_clause.condition
                )
            else:
                return False

        except Exception as e:
            # Fall back to simple condition parsing for backwards compatibility
            try:
                if (
                    "=" in condition_str
                    and " AND " not in condition_str
                    and " OR " not in condition_str
                ):
                    parts = condition_str.split("=", 1)
                    field = parts[0].strip()
                    value = parts[1].strip().strip("'\"")  # Remove quotes

                    item_value = self._get_nested_value(item, field)
                    return str(item_value) == value if item_value is not None else False
                elif (
                    "!=" in condition_str
                    and " AND " not in condition_str
                    and " OR " not in condition_str
                ):
                    parts = condition_str.split("!=", 1)
                    field = parts[0].strip()
                    value = parts[1].strip().strip("'\"")  # Remove quotes

                    item_value = self._get_nested_value(item, field)
                    return str(item_value) != value if item_value is not None else True
                else:
                    return False
            except Exception:
                return False

    def _evaluate_expression_dict(self, item: Dict, expr: Expression) -> bool:
        """Evaluate an expression against an item dictionary (for ARRAY_AGG conditions)"""
        if isinstance(expr, BinaryOp):
            if expr.operator == TokenType.AND:
                return self._evaluate_expression_dict(
                    item, expr.left
                ) and self._evaluate_expression_dict(item, expr.right)
            elif expr.operator == TokenType.OR:
                return self._evaluate_expression_dict(
                    item, expr.left
                ) or self._evaluate_expression_dict(item, expr.right)
            else:
                # Comparison operators
                left_val = self._get_value_dict(item, expr.left)
                # For comparison right side, handle FieldAccess as literal values
                if isinstance(expr.right, FieldAccess) and expr.right.path is None:
                    # Bare identifier on right side should be treated as literal
                    right_val = expr.right.field
                else:
                    right_val = self._get_value_dict(item, expr.right)
                return self._compare(left_val, expr.operator, right_val)

        elif isinstance(expr, UnaryOp):
            if expr.operator == TokenType.NOT:
                return not self._evaluate_expression_dict(item, expr.operand)

        elif isinstance(expr, FieldAccess):
            # Simple field existence check
            return self._get_value_dict(item, expr) is not None

        return False

    def _get_value_dict(self, item: Dict, expr: Expression) -> Any:
        """Get value from item dictionary based on expression (for ARRAY_AGG conditions)"""
        if isinstance(expr, FieldAccess):
            if expr.path:
                # Metadata or participants access
                if expr.field == "metadata" and expr.path:
                    value = item.get("metadata", {})
                    for part in expr.path:
                        if isinstance(value, dict) and part in value:
                            value = value[part]
                        else:
                            return None
                    return value
                elif expr.field == "participants" and expr.path:
                    value = item.get("participants", {})
                    for part in expr.path:
                        if isinstance(value, dict):
                            # Try exact case first, then lowercase for keywords that got uppercased
                            if part in value:
                                value = value[part]
                            elif part.lower() in value:
                                value = value[part.lower()]
                            else:
                                return None
                        else:
                            return None
                    return value
            else:
                # Entity access - return the value from item
                return item.get(expr.field)

        elif isinstance(expr, Literal):
            return expr.value

        elif isinstance(expr, Range):
            # Extract the actual values from the Range expressions
            start_val = self._get_value_dict(item, expr.start)
            end_val = self._get_value_dict(item, expr.end)
            return (start_val, end_val)

        elif isinstance(expr, ListExpression):
            return [self._get_literal_value(item) for item in expr.items]

        return None

    def _evaluate_having(self, grouped_result: Dict, having_expr: Expression) -> bool:
        """Evaluate HAVING clause on grouped results"""
        if isinstance(having_expr, BinaryOp):
            # Handle COUNT(*) and COUNT(DISTINCT field) function calls
            if (
                isinstance(having_expr.left, FunctionCall)
                and having_expr.left.name == "COUNT"
            ):
                # Check if this is COUNT(DISTINCT field)
                if (
                    len(having_expr.left.args) > 0
                    and isinstance(having_expr.left.args[0], Literal)
                    and str(having_expr.left.args[0].value).startswith("DISTINCT ")
                ):

                    # Extract field name from DISTINCT argument
                    field_name = str(having_expr.left.args[0].value)[
                        9:
                    ]  # Remove "DISTINCT "

                    # Count distinct values in the group
                    group = grouped_result.get("_group", [])
                    values = set()
                    for row in group:
                        value = self._get_nested_value(row, field_name)
                        if value is not None:
                            values.add(str(value))
                    count = len(values)
                else:
                    # Regular COUNT(*)
                    count = grouped_result.get("_count", 0)

                threshold = having_expr.right.value

                if having_expr.operator == TokenType.GT:
                    return count > threshold
                elif having_expr.operator == TokenType.LT:
                    return count < threshold
                elif having_expr.operator == TokenType.GTE:
                    return count >= threshold
                elif having_expr.operator == TokenType.LTE:
                    return count <= threshold
                elif having_expr.operator == TokenType.EQ:
                    return count == threshold
            # Handle field access (legacy code path)
            elif (
                hasattr(having_expr.left, "field")
                and having_expr.left.field == "_count"
            ):
                count = grouped_result.get("_count", 0)
                threshold = having_expr.right.value

                if having_expr.operator == TokenType.GT:
                    return count > threshold
                elif having_expr.operator == TokenType.LT:
                    return count < threshold
                elif having_expr.operator == TokenType.GTE:
                    return count >= threshold
                elif having_expr.operator == TokenType.LTE:
                    return count <= threshold
                elif having_expr.operator == TokenType.EQ:
                    return count == threshold

        return True

    def _get_sort_key(self, result: Dict, field: str) -> Any:
        """Get sort key for ORDER BY"""
        value = self._get_nested_value(result, field)
        if value is None:
            return ""

        # For arrays (from GROUP BY auto-aggregation), use the first element for sorting
        if isinstance(value, list) and value:
            return value[0]

        return value

    def _get_nested_value(self, result: Dict, field: str) -> Any:
        """Get nested value using dot notation"""
        parts = field.split(".")
        value = result
        for part in parts:
            if isinstance(value, dict):
                # Try exact case first, then lowercase for keywords that got uppercased
                if part in value:
                    value = value[part]
                elif part.lower() in value:
                    value = value[part.lower()]
                else:
                    return None
            else:
                return None
        return value

    def _apply_select(
        self, results: List[Dict], select_clause: SelectClause
    ) -> List[Dict]:
        """Apply SELECT clause to results"""
        if not results:
            return results

        selected_results = []
        for result in results:
            selected = {}

            for item, alias in select_clause.items:
                if item == "*":
                    selected = result.copy()
                elif item.startswith("COUNT("):
                    # Handle COUNT aggregate function
                    key = alias if alias else "count"

                    # Check if it's COUNT(DISTINCT field)
                    if "COUNT(DISTINCT " in item:
                        # Extract field name from COUNT(DISTINCT field)
                        field_part = item[len("COUNT(DISTINCT ") : -1].strip()

                        if "_group" in result:
                            # For grouped results, count distinct values of the field
                            group = result["_group"]
                            values = set()
                            for row in group:
                                value = self._get_nested_value(row, field_part)
                                if value is not None:
                                    values.add(
                                        str(value)
                                    )  # Convert to string for consistency
                            selected[key] = len(values)
                        else:
                            # For single row, distinct count is either 0 or 1
                            value = self._get_nested_value(result, field_part)
                            selected[key] = 1 if value is not None else 0
                    else:
                        # Regular COUNT(*) or COUNT(field)
                        if "_count" in result:
                            selected[key] = result["_count"]
                        else:
                            selected[key] = 1
                elif item.startswith("ARRAY_AGG("):
                    # Handle ARRAY_AGG aggregate function
                    key = alias if alias else "array_agg"

                    if "_group" in result:
                        # Parse ARRAY_AGG syntax
                        if " WHERE " in item:
                            # ARRAY_AGG(field WHERE condition)
                            parts = item[10:-1].split(
                                " WHERE ", 1
                            )  # Remove "ARRAY_AGG(" and ")"
                            field_name = parts[0].strip()
                            condition_str = parts[1].strip()

                            # Collect values that match the condition
                            values = []
                            seen = set()
                            for group_item in result["_group"]:
                                # Evaluate the condition for this item
                                if self._evaluate_array_agg_condition(
                                    group_item, condition_str
                                ):
                                    if field_name == "*":
                                        raise BIQLEvaluationError(
                                            "Wildcard (*) is not supported in ARRAY_AGG. Please specify a field name."
                                        )
                                    else:
                                        value = self._get_nested_value(
                                            group_item, field_name
                                        )

                                    if value is not None and value not in seen:
                                        values.append(value)
                                        seen.add(value)

                            selected[key] = sorted(values)
                        else:
                            # Regular ARRAY_AGG(field) or ARRAY_AGG(DISTINCT field)
                            field_match = item[10:-1]  # Remove "ARRAY_AGG(" and ")"

                            # Check for DISTINCT keyword
                            is_distinct = False
                            if field_match.startswith("DISTINCT "):
                                is_distinct = True
                                field_match = field_match[9:]  # Remove "DISTINCT "

                            values = []
                            seen = set()
                            for group_item in result["_group"]:
                                if field_match == "*":
                                    raise BIQLEvaluationError(
                                        "Wildcard (*) is not supported in ARRAY_AGG. Please specify a field name."
                                    )
                                else:
                                    value = self._get_nested_value(
                                        group_item, field_match
                                    )

                                if is_distinct:
                                    # For DISTINCT, only add non-None values if not seen
                                    if value is not None and value not in seen:
                                        values.append(value)
                                        seen.add(value)
                                else:
                                    # For non-DISTINCT, add all values including None
                                    values.append(value)

                            # Sort values, putting None values at the end
                            selected[key] = sorted(values, key=lambda x: (x is None, x))
                    else:
                        # Single row - return as single-item array
                        field_match = item[10:-1]  # Remove "ARRAY_AGG(" and ")"
                        if " WHERE " in field_match:
                            parts = field_match.split(" WHERE ", 1)
                            field_name = parts[0].strip()
                            condition_str = parts[1].strip()

                            if self._evaluate_array_agg_condition(
                                result, condition_str
                            ):
                                if field_name == "*":
                                    raise BIQLEvaluationError(
                                        "Wildcard (*) is not supported in ARRAY_AGG. Please specify a field name."
                                    )
                                else:
                                    value = self._get_nested_value(result, field_name)
                                selected[key] = [value] if value is not None else []
                            else:
                                selected[key] = []
                        else:
                            if field_match == "*":
                                raise BIQLEvaluationError(
                                    "Wildcard (*) is not supported in ARRAY_AGG. Please specify a field name."
                                )
                            else:
                                value = self._get_nested_value(result, field_match)
                            selected[key] = [value] if value is not None else []

                elif item.startswith("(") and item.endswith(")"):
                    # Handle parenthesized expressions for implicit aggregation
                    key = alias if alias else "array"

                    # Parse the parenthesized expression
                    inner = item[1:-1]  # Remove outer parentheses

                    # Check for DISTINCT
                    is_distinct = False
                    condition_str = None
                    field_name = inner

                    if inner.startswith("DISTINCT "):
                        is_distinct = True
                        inner = inner[9:]  # Remove "DISTINCT "
                        field_name = inner

                    # Check for WHERE clause
                    if " WHERE " in inner:
                        parts = inner.split(" WHERE ", 1)
                        field_name = parts[0].strip()
                        condition_str = parts[1].strip()

                        # Remove DISTINCT from field_name if it's there
                        if field_name.startswith("DISTINCT "):
                            is_distinct = True
                            field_name = field_name[9:]

                    if "_group" in result:
                        # Grouped results - collect array from group
                        values = []
                        seen = set()

                        for group_item in result["_group"]:
                            # Check condition if present
                            if (
                                condition_str
                                and not self._evaluate_array_agg_condition(
                                    group_item, condition_str
                                )
                            ):
                                continue

                            value = self._get_nested_value(group_item, field_name)
                            if is_distinct:
                                # For DISTINCT, only add non-None values if not seen
                                if value is not None and value not in seen:
                                    values.append(value)
                                    seen.add(value)
                            else:
                                # For non-DISTINCT, add all values including None
                                values.append(value)

                        # Sort values, putting None values at the end
                        selected[key] = sorted(values, key=lambda x: (x is None, x))
                    else:
                        # Single row - return as single-item array if condition matches
                        if condition_str and not self._evaluate_array_agg_condition(
                            result, condition_str
                        ):
                            selected[key] = []
                        else:
                            value = self._get_nested_value(result, field_name)
                            selected[key] = [value] if value is not None else []

                elif item.startswith(("AVG(", "MAX(", "MIN(", "SUM(")):
                    # Handle other aggregate functions
                    func_name = item.split("(")[0].lower()
                    # Extract field name from function call
                    field_match = item[
                        len(func_name) + 1 : -1
                    ]  # Remove function name and parentheses

                    if "_aggregates" in result and field_match in result["_aggregates"]:
                        key = alias if alias else func_name
                        if func_name in result["_aggregates"][field_match]:
                            selected[key] = result["_aggregates"][field_match][
                                func_name
                            ]
                        else:
                            selected[key] = None
                    else:
                        # If no aggregates, compute on the fly for single row
                        if "_group" not in result:
                            try:
                                value = self._get_nested_value(result, field_match)
                                if value is not None:
                                    num_value = float(value)
                                    key = alias if alias else func_name
                                    selected[key] = num_value
                                else:
                                    key = alias if alias else func_name
                                    selected[key] = None
                            except (ValueError, TypeError):
                                key = alias if alias else func_name
                                selected[key] = None
                        else:
                            key = alias if alias else func_name
                            selected[key] = None
                else:
                    # Handle regular field selection
                    key = alias if alias else item

                    # If grouped result, aggregate non-grouped fields into arrays
                    if "_group" in result:
                        # Check if this field is a grouping field
                        if (
                            item in result
                            and item != "_count"
                            and item != "_group"
                            and item != "_aggregates"
                        ):
                            # This is a GROUP BY field, use the single grouped value
                            selected[key] = result[item]
                        else:
                            # This is not a GROUP BY field, collect all values (including duplicates and None)
                            values = []
                            for group_item in result["_group"]:
                                value = self._get_nested_value(group_item, item)
                                values.append(value)

                            # Sort values, putting None values at the end
                            selected[key] = sorted(values, key=lambda x: (x is None, x))
                    else:
                        # Regular non-grouped result
                        value = self._get_nested_value(result, item)
                        selected[key] = value

            selected_results.append(selected)

        return selected_results

    def _apply_distinct(self, results: List[Dict]) -> List[Dict]:
        """Apply DISTINCT to remove duplicate rows"""
        if not results:
            return results

        # Convert each dict to a hashable representation
        seen = set()
        distinct_results = []

        for result in results:
            # Create a hashable key from the result dict, excluding internal fields
            # Sort items to ensure consistent ordering
            try:
                key = tuple(
                    sorted(
                        (k, tuple(v) if isinstance(v, list) else v)
                        for k, v in result.items()
                        if not k.startswith(
                            "_"
                        )  # Exclude internal fields like _file_paths
                    )
                )

                if key not in seen:
                    seen.add(key)
                    distinct_results.append(result)
            except TypeError:
                # If values aren't hashable, fall back to string comparison
                filtered_items = [
                    (k, v) for k, v in result.items() if not k.startswith("_")
                ]
                key = str(sorted(filtered_items))
                if key not in seen:
                    seen.add(key)
                    distinct_results.append(result)

        return distinct_results
