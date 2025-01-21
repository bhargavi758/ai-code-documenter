"""Factory that returns the correct analyzer for a given file extension."""

from __future__ import annotations

from pathlib import Path

from src.analyzer.base import BaseAnalyzer
from src.analyzer.python_analyzer import PythonAnalyzer
from src.analyzer.typescript_analyzer import TypeScriptAnalyzer

_ANALYZERS: list[BaseAnalyzer] = [
    PythonAnalyzer(),
    TypeScriptAnalyzer(),
]

SUPPORTED_EXTENSIONS: set[str] = set()
for _a in _ANALYZERS:
    SUPPORTED_EXTENSIONS.update(_a.SUPPORTED_EXTENSIONS)


def create_analyzer(filepath: Path) -> BaseAnalyzer | None:
    """Return an analyzer that can handle *filepath*, or ``None``."""
    for analyzer in _ANALYZERS:
        if analyzer.can_handle(filepath):
            return analyzer
    return None
