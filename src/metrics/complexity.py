"""Cyclomatic complexity calculator for Python AST nodes."""

from __future__ import annotations

import ast


_BRANCH_NODES = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.ExceptHandler,
    ast.With,
    ast.AsyncWith,
    ast.Assert,
)


class CyclomaticComplexityCalculator:
    """Counts decision points in a Python function to derive complexity.

    Complexity starts at 1 (the function itself is one path) and increments
    for every branch: ``if``, ``elif``, ``for``, ``while``, ``except``,
    ``with``, ``assert``, boolean ``and``/``or``.
    """

    @staticmethod
    def for_node(node: ast.AST) -> int:
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, _BRANCH_NODES):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity

    @classmethod
    def for_source(cls, source: str) -> dict[str, int]:
        """Return ``{function_name: complexity}`` for every function in *source*."""
        tree = ast.parse(source)
        results: dict[str, int] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                results[node.name] = cls.for_node(node)
        return results

    @staticmethod
    def risk_label(complexity: int) -> str:
        if complexity <= 5:
            return "low"
        if complexity <= 10:
            return "moderate"
        if complexity <= 20:
            return "high"
        return "very high"
