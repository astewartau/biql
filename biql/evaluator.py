"""
Query Evaluator for BIDS Query Language (BQL)

Evaluates parsed BQL queries against BIDS datasets.
"""

import fnmatch
import re
from collections import defaultdict
from typing import Any, Dict, List, Union
from .ast_nodes import *
from .dataset import BIDSDataset, BIDSFile
from .lexer import TokenType


class BQLEvaluationError(Exception):
    """Exception raised for BQL evaluation errors"""
    pass


class BQLEvaluator:
    """Evaluates BQL queries against BIDS datasets"""
    
    def __init__(self, dataset: BIDSDataset):
        self.dataset = dataset
        
    def evaluate(self, query: Query) -> List[Dict[str, Any]]:
        """Evaluate a query and return results"""
        # Start with all files
        results = self.dataset.files
        
        # Apply WHERE clause
        if query.where_clause:
            results = [f for f in results if self._evaluate_expression(f, query.where_clause.condition)]
            
        # Convert to dictionaries for further processing
        result_dicts = []
        for file in results:
            result_dict = self._file_to_dict(file)
            result_dicts.append(result_dict)
            
        # Apply GROUP BY
        if query.group_by:
            result_dicts = self._apply_group_by(result_dicts, query.group_by)
            
        # Apply HAVING
        if query.having:
            # Filter grouped results based on HAVING condition
            result_dicts = [r for r in result_dicts if self._evaluate_having(r, query.having)]
            
        # Apply ORDER BY
        if query.order_by:
            for field, direction in reversed(query.order_by):
                reverse = (direction == 'DESC')
                result_dicts.sort(key=lambda x: self._get_sort_key(x, field), reverse=reverse)
                
        # Apply SELECT
        if query.select_clause:
            result_dicts = self._apply_select(result_dicts, query.select_clause)
            
        return result_dicts
        
    def _file_to_dict(self, file: BIDSFile) -> Dict[str, Any]:
        """Convert BIDSFile to dictionary representation"""
        result_dict = {
            'filepath': str(file.filepath),
            'relative_path': str(file.relative_path),
            'filename': file.filepath.name,
            **file.entities,
            'metadata': file.metadata
        }
        
        # Add participant data if available
        if 'sub' in file.entities and file.entities['sub'] in self.dataset.participants:
            result_dict['participants'] = self.dataset.participants[file.entities['sub']]
            
        return result_dict
        
    def _evaluate_expression(self, file: BIDSFile, expr: Expression) -> bool:
        """Evaluate an expression against a file"""
        if isinstance(expr, BinaryOp):
            if expr.operator == TokenType.AND:
                return (self._evaluate_expression(file, expr.left) and 
                       self._evaluate_expression(file, expr.right))
            elif expr.operator == TokenType.OR:
                return (self._evaluate_expression(file, expr.left) or 
                       self._evaluate_expression(file, expr.right))
            else:
                # Comparison operators
                left_val = self._get_value(file, expr.left)
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
                if expr.field == 'metadata' and expr.path:
                    value = file.metadata
                    for part in expr.path:
                        if isinstance(value, dict) and part in value:
                            value = value[part]
                        else:
                            return None
                    return value
                elif expr.field == 'participants' and expr.path:
                    if 'sub' in file.entities and file.entities['sub'] in self.dataset.participants:
                        value = self.dataset.participants[file.entities['sub']]
                        for part in expr.path:
                            if isinstance(value, dict) and part in value:
                                value = value[part]
                            else:
                                return None
                        return value
                    return None
            else:
                # Entity access
                return file.entities.get(expr.field)
                
        elif isinstance(expr, Literal):
            return expr.value
            
        elif isinstance(expr, Range):
            return (expr.start, expr.end)
            
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
            
        # Handle IN operator with lists
        if operator == TokenType.IN and isinstance(right, list):
            return str(left) in [str(item) for item in right]
            
        # Convert types if needed for numeric comparison
        if isinstance(right, (int, float)) and isinstance(left, str):
            try:
                left = float(left) if '.' in left else int(left)
            except ValueError:
                # If conversion fails, fall back to string comparison
                pass
                
        # Range comparison
        if isinstance(right, tuple) and len(right) == 2:
            try:
                left_num = float(left) if isinstance(left, str) else left
                return right[0] <= left_num <= right[1]
            except (ValueError, TypeError):
                return False
                
        # String pattern matching for equality
        if operator == TokenType.EQ and isinstance(right, str):
            if '*' in right or '?' in right:
                return fnmatch.fnmatch(str(left), right)
                
        # Regular expression matching
        if operator == TokenType.MATCH and isinstance(right, str):
            try:
                # Remove regex delimiters if present
                pattern = right
                if pattern.startswith('/') and pattern.endswith('/'):
                    pattern = pattern[1:-1]
                return bool(re.match(pattern, str(left)))
            except re.error:
                return False
                
        # LIKE operator (SQL-style pattern matching)
        if operator == TokenType.LIKE and isinstance(right, str):
            # Convert SQL LIKE pattern to fnmatch pattern
            pattern = right.replace('%', '*').replace('_', '?')
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
            except:
                return False
            
        return False
        
    def _apply_group_by(self, results: List[Dict], group_fields: List[str]) -> List[Dict]:
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
            agg_result['_count'] = len(group)
            agg_result['_group'] = group
            aggregated.append(agg_result)
            
        return aggregated
        
    def _evaluate_having(self, grouped_result: Dict, having_expr: Expression) -> bool:
        """Evaluate HAVING clause on grouped results"""
        # For now, implement basic functionality
        # This would need to be extended for full HAVING support
        if isinstance(having_expr, BinaryOp):
            if having_expr.left.field == '_count':
                count = grouped_result.get('_count', 0)
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
            return ''
        return value
        
    def _get_nested_value(self, result: Dict, field: str) -> Any:
        """Get nested value using dot notation"""
        parts = field.split('.')
        value = result
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None
        return value
        
    def _apply_select(self, results: List[Dict], select_clause: SelectClause) -> List[Dict]:
        """Apply SELECT clause to results"""
        if not results:
            return results
            
        selected_results = []
        for result in results:
            selected = {}
            
            for item, alias in select_clause.items:
                if item == '*':
                    selected = result.copy()
                elif item.startswith('COUNT('):
                    # Handle aggregate functions
                    if '_count' in result:
                        key = alias if alias else 'count'
                        selected[key] = result['_count']
                    else:
                        key = alias if alias else 'count'
                        selected[key] = 1
                else:
                    # Handle regular field selection
                    value = self._get_nested_value(result, item)
                    key = alias if alias else item
                    selected[key] = value
                    
            selected_results.append(selected)
            
        return selected_results