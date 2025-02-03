"""Tests for cyclomatic complexity calculation."""

from __future__ import annotations

import pytest

from src.metrics.complexity import CyclomaticComplexityCalculator


class TestCyclomaticComplexity:
    def test_simple_function(self) -> None:
        source = "def hello():\n    return 'hi'\n"
        results = CyclomaticComplexityCalculator.for_source(source)
        assert results["hello"] == 1

    def test_single_if(self) -> None:
        source = (
            "def check(x):\n"
            "    if x > 0:\n"
            "        return 'positive'\n"
            "    return 'non-positive'\n"
        )
        results = CyclomaticComplexityCalculator.for_source(source)
        assert results["check"] == 2

    def test_if_elif_else(self) -> None:
        source = (
            "def classify(x):\n"
            "    if x > 0:\n"
            "        return 'pos'\n"
            "    elif x == 0:\n"
            "        return 'zero'\n"
            "    else:\n"
            "        return 'neg'\n"
        )
        results = CyclomaticComplexityCalculator.for_source(source)
        assert results["classify"] == 3

    def test_for_loop(self) -> None:
        source = (
            "def total(items):\n"
            "    s = 0\n"
            "    for i in items:\n"
            "        s += i\n"
            "    return s\n"
        )
        results = CyclomaticComplexityCalculator.for_source(source)
        assert results["total"] == 2

    def test_while_loop(self) -> None:
        source = (
            "def countdown(n):\n"
            "    while n > 0:\n"
            "        n -= 1\n"
        )
        results = CyclomaticComplexityCalculator.for_source(source)
        assert results["countdown"] == 2

    def test_try_except(self) -> None:
        source = (
            "def safe_div(a, b):\n"
            "    try:\n"
            "        return a / b\n"
            "    except ZeroDivisionError:\n"
            "        return None\n"
        )
        results = CyclomaticComplexityCalculator.for_source(source)
        assert results["safe_div"] == 2

    def test_boolean_operators(self) -> None:
        source = (
            "def valid(x, y):\n"
            "    return x > 0 and y > 0 and x != y\n"
        )
        results = CyclomaticComplexityCalculator.for_source(source)
        assert results["valid"] == 3

    def test_complex_function(self) -> None:
        source = (
            "def process(items):\n"
            "    for item in items:\n"
            "        if item > 0:\n"
            "            if item % 2 == 0:\n"
            "                yield item\n"
            "        elif item == 0:\n"
            "            continue\n"
        )
        results = CyclomaticComplexityCalculator.for_source(source)
        assert results["process"] >= 4


class TestRiskLabel:
    @pytest.mark.parametrize("complexity,expected", [
        (1, "low"),
        (5, "low"),
        (6, "moderate"),
        (10, "moderate"),
        (11, "high"),
        (20, "high"),
        (21, "very high"),
    ])
    def test_labels(self, complexity: int, expected: str) -> None:
        assert CyclomaticComplexityCalculator.risk_label(complexity) == expected
