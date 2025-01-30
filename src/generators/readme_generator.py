"""Generates a project README.md from analyzed code structure."""

from __future__ import annotations

from src.generators.base import BaseGenerator
from src.models.code_elements import ModuleInfo, ProjectInfo, Visibility
from src.utils.formatting import MarkdownFormatter as Fmt


class ReadmeGenerator(BaseGenerator):
    def generate(self, project: ProjectInfo) -> str:
        sections: list[str] = [
            self._header(project),
            self._table_of_contents(),
            self._overview(project),
            self._installation(project),
            self._project_structure(project),
            self._modules_section(project),
            self._quick_start(project),
            self._statistics(project),
        ]
        return "\n\n".join(s for s in sections if s)

    # ------------------------------------------------------------------
    # Sections
    # ------------------------------------------------------------------

    def _header(self, project: ProjectInfo) -> str:
        lines = [Fmt.heading(project.name, level=1)]
        if project.description:
            lines.append(project.description)
        languages = ", ".join(sorted(project.languages)) if project.languages else "N/A"
        lines.append(f"\n**Languages:** {languages}  ")
        if project.version:
            lines.append(f"**Version:** {project.version}  ")
        return "\n".join(lines)

    @staticmethod
    def _table_of_contents() -> str:
        items = [
            "Overview", "Installation", "Project Structure",
            "Modules", "Quick Start", "Statistics",
        ]
        toc = [Fmt.heading("Table of Contents", level=2)]
        toc.extend(f"- [{item}](#{item.lower().replace(' ', '-')})" for item in items)
        return "\n".join(toc)

    @staticmethod
    def _overview(project: ProjectInfo) -> str:
        lines = [Fmt.heading("Overview", level=2)]
        lines.append(
            f"This project contains **{project.total_files}** source files "
            f"with **{project.total_classes}** classes and "
            f"**{project.total_functions}** top-level functions "
            f"across **{project.total_lines}** lines of code."
        )
        return "\n".join(lines)

    @staticmethod
    def _installation(project: ProjectInfo) -> str:
        lines = [Fmt.heading("Installation", level=2)]
        has_python = any(m.language == "python" for m in project.modules)
        has_ts = any(m.language == "typescript" for m in project.modules)

        if has_python:
            lines.append(Fmt.code_block("pip install -r requirements.txt", language="bash"))
        if has_ts:
            lines.append(Fmt.code_block("npm install", language="bash"))
        if not has_python and not has_ts:
            lines.append("See project documentation for installation instructions.")
        return "\n".join(lines)

    @staticmethod
    def _project_structure(project: ProjectInfo) -> str:
        lines = [Fmt.heading("Project Structure", level=2)]
        tree_lines: list[str] = []
        for module in sorted(project.modules, key=lambda m: str(m.filepath)):
            try:
                relative = module.filepath.relative_to(project.root)
            except ValueError:
                relative = module.filepath
            tree_lines.append(str(relative))
        lines.append(Fmt.code_block("\n".join(tree_lines), language="text"))
        return "\n".join(lines)

    def _modules_section(self, project: ProjectInfo) -> str:
        lines = [Fmt.heading("Modules", level=2)]
        for module in sorted(project.modules, key=lambda m: str(m.filepath)):
            lines.append(self._module_summary(module, project))
        return "\n\n".join(lines)

    @staticmethod
    def _module_summary(module: ModuleInfo, project: ProjectInfo) -> str:
        try:
            relative = module.filepath.relative_to(project.root)
        except ValueError:
            relative = module.filepath
        lines = [Fmt.heading(f"`{relative}`", level=3)]

        if module.docstring:
            lines.append(module.docstring.split("\n")[0])

        if module.classes:
            lines.append("\n**Classes:**\n")
            for cls in module.classes:
                desc = cls.docstring.split("\n")[0] if cls.docstring else ""
                method_count = len(cls.public_methods)
                lines.append(f"- **`{cls.name}`** — {desc} ({method_count} public methods)")

        public_fns = module.public_functions
        if public_fns:
            lines.append("\n**Functions:**\n")
            for fn in public_fns:
                desc = fn.docstring.split("\n")[0] if fn.docstring else ""
                lines.append(f"- `{fn.signature}` — {desc}")

        return "\n".join(lines)

    @staticmethod
    def _quick_start(project: ProjectInfo) -> str:
        lines = [Fmt.heading("Quick Start", level=2)]
        exported: list[str] = []
        for module in project.modules:
            for fn in module.public_functions[:2]:
                if fn.visibility == Visibility.PUBLIC and not fn.is_dunder:
                    exported.append(f"from {module.name} import {fn.name}")
        if exported:
            lines.append(Fmt.code_block("\n".join(exported[:6]), language="python"))
        else:
            lines.append("See individual module documentation for usage examples.")
        return "\n".join(lines)

    @staticmethod
    def _statistics(project: ProjectInfo) -> str:
        lines = [Fmt.heading("Statistics", level=2)]
        total_code = sum(m.lines_of_code for m in project.modules)
        total_blank = sum(m.blank_lines for m in project.modules)
        total_comment = sum(m.comment_lines for m in project.modules)
        rows = [
            ("Total files", str(project.total_files)),
            ("Lines of code", str(total_code)),
            ("Blank lines", str(total_blank)),
            ("Comment lines", str(total_comment)),
            ("Classes", str(project.total_classes)),
            ("Functions", str(project.total_functions)),
            ("Languages", ", ".join(sorted(project.languages))),
        ]
        lines.append(Fmt.table(["Metric", "Value"], rows))
        return "\n".join(lines)
