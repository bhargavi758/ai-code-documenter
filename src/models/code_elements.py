"""Data models representing extracted code structure elements.

Every parsed source file is decomposed into these dataclasses, forming a
language-agnostic intermediate representation that generators consume.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Visibility(Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"


@dataclass(frozen=True)
class Parameter:
    name: str
    annotation: str | None = None
    default: str | None = None
    is_optional: bool = False

    @property
    def display(self) -> str:
        parts = [self.name]
        if self.annotation:
            parts.append(f": {self.annotation}")
        if self.default:
            parts.append(f" = {self.default}")
        return "".join(parts)


@dataclass
class FunctionDef:
    name: str
    params: list[Parameter] = field(default_factory=list)
    return_type: str | None = None
    docstring: str | None = None
    decorators: list[str] = field(default_factory=list)
    is_async: bool = False
    is_method: bool = False
    is_static: bool = False
    is_classmethod: bool = False
    is_property: bool = False
    visibility: Visibility = Visibility.PUBLIC
    line_number: int = 0
    end_line_number: int = 0
    complexity: int = 1

    @property
    def signature(self) -> str:
        prefix = "async " if self.is_async else ""
        params_str = ", ".join(p.display for p in self.params)
        ret = f" -> {self.return_type}" if self.return_type else ""
        return f"{prefix}def {self.name}({params_str}){ret}"

    @property
    def is_private(self) -> bool:
        return self.name.startswith("_") and not self.name.startswith("__")

    @property
    def is_dunder(self) -> bool:
        return self.name.startswith("__") and self.name.endswith("__")


@dataclass
class ClassDef:
    name: str
    bases: list[str] = field(default_factory=list)
    methods: list[FunctionDef] = field(default_factory=list)
    docstring: str | None = None
    decorators: list[str] = field(default_factory=list)
    is_abstract: bool = False
    line_number: int = 0
    end_line_number: int = 0

    @property
    def public_methods(self) -> list[FunctionDef]:
        return [m for m in self.methods if m.visibility == Visibility.PUBLIC and not m.is_dunder]

    @property
    def properties(self) -> list[FunctionDef]:
        return [m for m in self.methods if m.is_property]


@dataclass(frozen=True)
class ImportInfo:
    module: str
    names: list[str] = field(default_factory=list)
    alias: str | None = None
    is_from_import: bool = False
    line_number: int = 0

    @property
    def display(self) -> str:
        if self.is_from_import:
            names_str = ", ".join(self.names) if self.names else "*"
            return f"from {self.module} import {names_str}"
        alias_part = f" as {self.alias}" if self.alias else ""
        return f"import {self.module}{alias_part}"


@dataclass
class TypeAlias:
    """Represents a TypeScript type alias or interface."""
    name: str
    definition: str
    is_exported: bool = False
    line_number: int = 0


@dataclass
class ModuleInfo:
    filepath: Path
    language: str
    docstring: str | None = None
    classes: list[ClassDef] = field(default_factory=list)
    functions: list[FunctionDef] = field(default_factory=list)
    imports: list[ImportInfo] = field(default_factory=list)
    type_aliases: list[TypeAlias] = field(default_factory=list)
    lines_of_code: int = 0
    blank_lines: int = 0
    comment_lines: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def name(self) -> str:
        return self.filepath.stem

    @property
    def total_lines(self) -> int:
        return self.lines_of_code + self.blank_lines + self.comment_lines

    @property
    def public_functions(self) -> list[FunctionDef]:
        return [f for f in self.functions if f.visibility == Visibility.PUBLIC]

    @property
    def all_functions(self) -> list[FunctionDef]:
        methods = [m for c in self.classes for m in c.methods]
        return self.functions + methods

    @property
    def average_complexity(self) -> float:
        fns = self.all_functions
        if not fns:
            return 0.0
        return sum(f.complexity for f in fns) / len(fns)


@dataclass
class ProjectInfo:
    root: Path
    name: str
    description: str = ""
    version: str = ""
    modules: list[ModuleInfo] = field(default_factory=list)

    @property
    def total_files(self) -> int:
        return len(self.modules)

    @property
    def total_lines(self) -> int:
        return sum(m.total_lines for m in self.modules)

    @property
    def total_classes(self) -> int:
        return sum(len(m.classes) for m in self.modules)

    @property
    def total_functions(self) -> int:
        return sum(len(m.functions) for m in self.modules)

    @property
    def languages(self) -> set[str]:
        return {m.language for m in self.modules}

    def get_modules_by_language(self, language: str) -> list[ModuleInfo]:
        return [m for m in self.modules if m.language == language]
