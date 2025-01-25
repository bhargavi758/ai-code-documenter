"""Aggregate code statistics across a project."""

from __future__ import annotations

from dataclasses import dataclass

from src.models.code_elements import ProjectInfo


@dataclass
class CodeStatistics:
    total_files: int = 0
    total_lines: int = 0
    code_lines: int = 0
    blank_lines: int = 0
    comment_lines: int = 0
    total_classes: int = 0
    total_functions: int = 0
    total_methods: int = 0
    average_complexity: float = 0.0
    max_complexity: int = 0
    max_complexity_function: str = ""
    languages: set[str] | None = None

    @classmethod
    def from_project(cls, project: ProjectInfo) -> CodeStatistics:
        stats = cls()
        stats.total_files = project.total_files
        stats.total_classes = project.total_classes
        stats.total_functions = project.total_functions
        stats.languages = project.languages

        all_complexities: list[int] = []
        max_c = 0
        max_c_name = ""

        for module in project.modules:
            stats.code_lines += module.lines_of_code
            stats.blank_lines += module.blank_lines
            stats.comment_lines += module.comment_lines

            for fn in module.all_functions:
                all_complexities.append(fn.complexity)
                if fn.complexity > max_c:
                    max_c = fn.complexity
                    max_c_name = f"{module.name}.{fn.name}"

            stats.total_methods += sum(len(c.methods) for c in module.classes)

        stats.total_lines = stats.code_lines + stats.blank_lines + stats.comment_lines
        stats.max_complexity = max_c
        stats.max_complexity_function = max_c_name
        if all_complexities:
            stats.average_complexity = round(sum(all_complexities) / len(all_complexities), 2)

        return stats

    def format_report(self) -> str:
        langs = ", ".join(sorted(self.languages)) if self.languages else "N/A"
        return (
            f"Files:            {self.total_files}\n"
            f"Languages:        {langs}\n"
            f"Lines (total):    {self.total_lines}\n"
            f"  Code:           {self.code_lines}\n"
            f"  Comments:       {self.comment_lines}\n"
            f"  Blank:          {self.blank_lines}\n"
            f"Classes:          {self.total_classes}\n"
            f"Functions:        {self.total_functions}\n"
            f"Methods:          {self.total_methods}\n"
            f"Avg complexity:   {self.average_complexity}\n"
            f"Max complexity:   {self.max_complexity} ({self.max_complexity_function})"
        )
