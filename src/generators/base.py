"""Abstract base class for documentation generators."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from src.models.code_elements import ProjectInfo


class BaseGenerator(ABC):
    """All generators accept a ``ProjectInfo`` and produce documentation."""

    @abstractmethod
    def generate(self, project: ProjectInfo) -> str:
        """Return the generated documentation as a string."""

    def write(self, project: ProjectInfo, output_path: Path) -> Path:
        """Generate documentation and write it to *output_path*."""
        content = self.generate(project)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        return output_path
