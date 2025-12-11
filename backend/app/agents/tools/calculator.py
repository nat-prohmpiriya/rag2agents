"""Calculator tool for safe mathematical expression evaluation."""

import ast
import logging
import math
import operator
from typing import Any

from app.agents.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


# Safe operators for evaluation
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

# Safe math functions
SAFE_FUNCTIONS = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sum": sum,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "floor": math.floor,
    "ceil": math.ceil,
    "pi": math.pi,
    "e": math.e,
}


class SafeEvaluator(ast.NodeVisitor):
    """Safe AST evaluator for mathematical expressions."""

    def visit_Expression(self, node: ast.Expression) -> Any:
        return self.visit(node.body)

    def visit_Constant(self, node: ast.Constant) -> Any:
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant type: {type(node.value)}")

    def visit_Num(self, node: ast.Num) -> Any:
        # For Python < 3.8 compatibility
        return node.n

    def visit_Name(self, node: ast.Name) -> Any:
        if node.id in SAFE_FUNCTIONS:
            value = SAFE_FUNCTIONS[node.id]
            if callable(value):
                raise ValueError(f"Function '{node.id}' must be called with arguments")
            return value
        raise ValueError(f"Unknown variable: {node.id}")

    def visit_BinOp(self, node: ast.BinOp) -> Any:
        left = self.visit(node.left)
        right = self.visit(node.right)
        op_type = type(node.op)

        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")

        # Prevent division by zero
        if op_type in (ast.Div, ast.FloorDiv, ast.Mod) and right == 0:
            raise ValueError("Division by zero")

        return SAFE_OPERATORS[op_type](left, right)

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
        operand = self.visit(node.operand)
        op_type = type(node.op)

        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")

        return SAFE_OPERATORS[op_type](operand)

    def visit_Call(self, node: ast.Call) -> Any:
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only simple function calls are supported")

        func_name = node.func.id
        if func_name not in SAFE_FUNCTIONS:
            raise ValueError(f"Unknown function: {func_name}")

        func = SAFE_FUNCTIONS[func_name]
        if not callable(func):
            raise ValueError(f"'{func_name}' is not callable")

        args = [self.visit(arg) for arg in node.args]
        return func(*args)

    def generic_visit(self, node: ast.AST) -> Any:
        raise ValueError(f"Unsupported expression type: {type(node).__name__}")


def safe_eval(expression: str) -> float | int:
    """Safely evaluate a mathematical expression.

    Args:
        expression: Mathematical expression string

    Returns:
        Calculated result

    Raises:
        ValueError: If expression is invalid or contains unsafe operations
    """
    try:
        tree = ast.parse(expression, mode="eval")
        evaluator = SafeEvaluator()
        result = evaluator.visit(tree)

        # Ensure result is a number
        if not isinstance(result, (int, float)):
            raise ValueError(f"Result is not a number: {type(result)}")

        return result
    except SyntaxError as e:
        raise ValueError(f"Invalid expression syntax: {e}")


class CalculatorTool(BaseTool):
    """Tool for safely evaluating mathematical expressions."""

    name = "calculator"
    description = "Evaluate mathematical expressions safely"

    async def execute(
        self,
        expression: str,
        **kwargs: Any,
    ) -> ToolResult:
        """Execute calculation.

        Args:
            expression: Mathematical expression to evaluate
                       Supports: +, -, *, /, //, %, **
                       Functions: sqrt, sin, cos, tan, log, log10, exp,
                                 floor, ceil, abs, round, min, max, sum
                       Constants: pi, e

        Returns:
            ToolResult with calculated value
        """
        if not expression or not expression.strip():
            return ToolResult(
                success=False,
                error="No expression provided",
            )

        try:
            # Clean expression
            expression = expression.strip()

            # Evaluate safely
            result = safe_eval(expression)

            return ToolResult(
                success=True,
                data=result,
                metadata={"expression": expression},
            )
        except ValueError as e:
            return ToolResult(
                success=False,
                error=str(e),
                metadata={"expression": expression},
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Calculation error: {str(e)}",
                metadata={"expression": expression},
            )

    def _get_parameters_schema(self) -> dict[str, Any]:
        """Get parameters schema for calculator tool."""
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate (e.g., '2 + 2', 'sqrt(16)', 'sin(pi/2)')",
                },
            },
            "required": ["expression"],
        }


# Singleton instance
calculator_tool = CalculatorTool()
