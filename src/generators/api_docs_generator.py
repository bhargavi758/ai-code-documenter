"""Generates detailed API reference documentation in Markdown."""

from __future__ import annotations

from src.generators.base import BaseGenerator
from src.models.code_elements import ClassDef, FunctionDef, ModuleInfo, ProjectInfo
from src.utils.formatting import MarkdownFormatter as Fmt


class ApiDocsGenerator(BaseGenerator):
    def generate(self, project: ProjectInfo) -> str:
        sections: list[str] = [
            Fmt.heading(f"{project.name} — API Reference", level=1),
            self._toc(project),
        ]
        for module in sorted(project.modules, key=lambda m: str(m.filepath)):
            sections.append(self._module_docs(module, project))
        return "\n\n---\n\n".join(s for s in sections if s)

    # ------------------------------------------------------------------
    # Table of contents
    # ------------------------------------------------------------------

    @staticmethod
    def _toc(project: ProjectInfo) -> str:
        lines = [Fmt.heading("Modules", level=2)]
        for module in sorted(project.modules, key=lambda m: str(m.filepath)):
            try:
                rel = module.filepath.relative_to(project.root)
            except ValueError:
                rel = module.filepath
            anchor = str(rel).replace("/", "").replace(".", "").replace("_", "-").lower()
            lines.append(f"- [`{rel}`](#{anchor})")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Per-module documentation
    # ------------------------------------------------------------------

    def _module_docs(self, module: ModuleInfo, project: ProjectInfo) -> str:
        try:
            rel = module.filepath.relative_to(project.root)
        except ValueError:
            rel = module.filepath
        lines = [Fmt.heading(f"Module `{rel}`", level=2)]

        if module.docstring:
            lines.append(module.docstring)

        if module.imports:
            lines.append(Fmt.heading("Imports", level=3))
            lines.extend(f"- `{imp.display}`" for imp in module.imports)

        for cls in module.classes:
            lines.append(self._class_docs(cls))

        for fn in module.functions:
            lines.append(self._function_docs(fn))

        return "\n\n".join(lines)

    # ------------------------------------------------------------------
    # Class documentation
    # ------------------------------------------------------------------

    def _class_docs(self, cls: ClassDef) -> str:
        bases_str = f"({', '.join(cls.bases)})" if cls.bases else ""
        lines = [Fmt.heading(f"class `{cls.name}{bases_str}`", level=3)]

        if cls.decorators:
            lines.append("**Decorators:** " + ", ".join(f"`@{d}`" for d in cls.decorators))

        if cls.docstring:
            lines.append(cls.docstring)

        for method in cls.methods:
            lines.append(self._function_docs(method, heading_level=4))

        return "\n\n".join(lines)

    # ------------------------------------------------------------------
    # Function documentation
    # ------------------------------------------------------------------

    @staticmethod
    def _function_docs(fn: FunctionDef, heading_level: int = 3) -> str:
        lines = [Fmt.heading(f"`{fn.signature}`", level=heading_level)]

        meta: list[str] = []
        if fn.decorators:
            meta.append("**Decorators:** " + ", ".join(f"`@{d}`" for d in fn.decorators))
        if fn.is_async:
            meta.append("**Async:** yes")
        meta.append(f"**Complexity:** {fn.complexity}")
        meta.append(f"**Lines:** {fn.line_number}–{fn.end_line_number}")
        lines.append("  \n".join(meta))

        if fn.docstring:
            lines.append(fn.docstring)

        if fn.params:
            lines.append("**Parameters:**\n")
            for p in fn.params:
                type_hint = f" (`{p.annotation}`)" if p.annotation else ""
                default = f" — default: `{p.default}`" if p.default else ""
                lines.append(f"- **{p.name}**{type_hint}{default}")

        if fn.return_type:
            lines.append(f"\n**Returns:** `{fn.return_type}`")

        return "\n".join(lines)
