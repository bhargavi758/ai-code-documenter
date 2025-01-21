"""Abstract base class for language-specific code analyzers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from src.models.code_elements import ModuleInfo


class BaseAnalyzer(ABC):
    """Contract that every language analyzer must implement.

    Subclasses are responsible for parsing a single source file and returning
    a fully populated ``ModuleInfo`` with classes, functions, imports, and
    line-count statistics.
    """

    SUPPORTED_EXTENSIONS: tuple[str, ...] = ()

    @abstractmethod
    def analyze_file(self, filepath: Path) -> ModuleInfo:
        """Parse *filepath* and return structured module information.

        Implementations must handle syntax errors gracefully — a malformed
        file should produce a ``ModuleInfo`` with errors populated rather
        than raising an exception.
        """

    def can_handle(self, filepath: Path) -> bool:
        return filepath.suffix in self.SUPPORTED_EXTENSIONS
