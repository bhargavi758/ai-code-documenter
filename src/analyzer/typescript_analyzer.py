"""TypeScript / JavaScript analyzer using regex-based parsing.

A full TS parser would require a Node.js dependency.  Instead we use
carefully crafted regular expressions that handle the most common
declaration patterns seen in production codebases.
"""

from __future__ import annotations

import re
from pathlib import Path

from src.analyzer.base import BaseAnalyzer
from src.models.code_elements import (
    ClassDef,
    FunctionDef,
    ImportInfo,
    ModuleInfo,
    Parameter,
    TypeAlias,
    Visibility,
)

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

_IMPORT_RE = re.compile(
    r"""^import\s+"""
    r"""(?:(?P<default>\w+)\s*,?\s*)?"""
    r"""(?:\{(?P<named>[^}]+)\}\s*)?"""
    r"""(?:from\s+)?['"](?P<module>[^'"]+)['"]""",
    re.MULTILINE,
)

_FUNCTION_RE = re.compile(
    r"""^(?P<export>export\s+)?"""
    r"""(?P<async>async\s+)?"""
    r"""function\s+(?P<name>\w+)"""
    r"""(?:<[^>]+>)?"""
    r"""\((?P<params>[^)]*)\)"""
    r"""(?:\s*:\s*(?P<return>[^\s{]+))?""",
    re.MULTILINE,
)

_ARROW_FN_RE = re.compile(
    r"""^(?P<export>export\s+)?"""
    r"""(?:const|let|var)\s+(?P<name>\w+)"""
    r"""(?:\s*:\s*[^=]+)?"""
    r"""\s*=\s*"""
    r"""(?P<async>async\s+)?"""
    r"""(?:<[^>]*(?:<[^>]*>[^>]*)*>\s*)?"""
    r"""\((?P<params>[^)]*)\)"""
    r"""(?:\s*:\s*(?P<return>[^\s=>]+))?\s*=>""",
    re.MULTILINE,
)

_CLASS_RE = re.compile(
    r"""^(?P<export>export\s+)?"""
    r"""(?:abstract\s+)?"""
    r"""class\s+(?P<name>\w+)"""
    r"""(?:<[^>]+>)?"""
    r"""(?:\s+extends\s+(?P<base>\w+)(?:<[^>]+>)?)?"""
    r"""(?:\s+implements\s+(?P<ifaces>[^{]+))?""",
    re.MULTILINE,
)

_METHOD_RE = re.compile(
    r"""^\s+(?P<access>public|private|protected)?\s*"""
    r"""(?P<static>static\s+)?"""
    r"""(?P<async>async\s+)?"""
    r"""(?P<name>\w+)"""
    r"""(?:<[^>]+>)?"""
    r"""\((?P<params>[^)]*)\)"""
    r"""(?:\s*:\s*(?P<return>[^\s{]+))?""",
    re.MULTILINE,
)

_INTERFACE_RE = re.compile(
    r"""^(?P<export>export\s+)?"""
    r"""interface\s+(?P<name>\w+)"""
    r"""(?:<[^>]+>)?"""
    r"""(?:\s+extends\s+(?P<base>[^{]+))?""",
    re.MULTILINE,
)

_TYPE_ALIAS_RE = re.compile(
    r"""^(?P<export>export\s+)?"""
    r"""type\s+(?P<name>\w+)"""
    r"""(?:<[^>]+>)?\s*=\s*(?P<def>.+)""",
    re.MULTILINE,
)


class TypeScriptAnalyzer(BaseAnalyzer):
    SUPPORTED_EXTENSIONS = (".ts", ".tsx", ".js", ".jsx")

    def analyze_file(self, filepath: Path) -> ModuleInfo:
        source = filepath.read_text(encoding="utf-8")
        module = ModuleInfo(filepath=filepath, language="typescript")
        self._count_lines(source, module)

        module.imports = self._extract_imports(source)
        module.functions = self._extract_functions(source)
        module.classes = self._extract_classes(source)
        module.type_aliases = self._extract_type_aliases(source)

        return module

    # ------------------------------------------------------------------
    # Imports
    # ------------------------------------------------------------------

    def _extract_imports(self, source: str) -> list[ImportInfo]:
        imports: list[ImportInfo] = []
        for match in _IMPORT_RE.finditer(source):
            names: list[str] = []
            if match.group("default"):
                names.append(match.group("default"))
            if match.group("named"):
                names.extend(n.strip().split(" as ")[0] for n in match.group("named").split(",") if n.strip())
            imports.append(ImportInfo(
                module=match.group("module"),
                names=names,
                is_from_import=True,
                line_number=source[:match.start()].count("\n") + 1,
            ))
        return imports

    # ------------------------------------------------------------------
    # Functions (both `function` keyword and arrow)
    # ------------------------------------------------------------------

    def _extract_functions(self, source: str) -> list[FunctionDef]:
        functions: list[FunctionDef] = []
        seen_names: set[str] = set()

        for pattern in (_FUNCTION_RE, _ARROW_FN_RE):
            for match in pattern.finditer(source):
                name = match.group("name")
                if name in seen_names:
                    continue
                seen_names.add(name)

                params = self._parse_params(match.group("params") or "")
                is_exported = bool(match.group("export"))

                functions.append(FunctionDef(
                    name=name,
                    params=params,
                    return_type=match.group("return"),
                    is_async=bool(match.group("async")),
                    visibility=Visibility.PUBLIC if is_exported else Visibility.PRIVATE,
                    line_number=source[:match.start()].count("\n") + 1,
                ))

        functions.extend(self._extract_generic_arrow_functions(source, seen_names))
        return functions

    def _extract_generic_arrow_functions(
        self, source: str, seen_names: set[str]
    ) -> list[FunctionDef]:
        """Handle arrow functions with generic type params like ``<T extends ...>``."""
        results: list[FunctionDef] = []
        pattern = re.compile(
            r"^(?P<export>export\s+)?(?:const|let|var)\s+(?P<name>\w+)\s*"
            r"(?::\s*[^=]+)?\s*=\s*(?P<async>async\s+)?<",
            re.MULTILINE,
        )
        for match in pattern.finditer(source):
            name = match.group("name")
            if name in seen_names:
                continue

            angle_start = match.end() - 1
            angle_end = self._skip_balanced(source, angle_start, "<", ">")
            if angle_end == -1:
                continue

            rest = source[angle_end + 1:].lstrip()
            if not rest.startswith("("):
                continue

            paren_start = angle_end + 1 + (len(source[angle_end + 1:]) - len(rest))
            paren_end = self._skip_balanced(source, paren_start, "(", ")")
            if paren_end == -1:
                continue

            raw_params = source[paren_start + 1:paren_end]
            after_paren = source[paren_end + 1:].lstrip()

            return_type = None
            if after_paren.startswith(":"):
                colon_rest = after_paren[1:].lstrip()
                arrow_idx = colon_rest.find("=>")
                if arrow_idx > 0:
                    return_type = colon_rest[:arrow_idx].strip()

            if "=>" not in source[paren_end:paren_end + 200]:
                continue

            seen_names.add(name)
            results.append(FunctionDef(
                name=name,
                params=self._parse_params(raw_params),
                return_type=return_type,
                is_async=bool(match.group("async")),
                visibility=Visibility.PUBLIC if match.group("export") else Visibility.PRIVATE,
                line_number=source[:match.start()].count("\n") + 1,
            ))
        return results

    @staticmethod
    def _skip_balanced(source: str, start: int, open_ch: str, close_ch: str) -> int:
        """Return the index of the matching *close_ch*, or -1.

        When matching ``<`` / ``>``, the ``>`` in ``=>`` is ignored so
        TypeScript arrow return types inside generics don't break the scan.
        """
        depth = 0
        i = start
        while i < len(source):
            ch = source[i]
            if ch == open_ch:
                if not (open_ch == "<" and i > 0 and source[i - 1] == "="):
                    depth += 1
            elif ch == close_ch:
                if close_ch == ">" and i > 0 and source[i - 1] == "=":
                    i += 1
                    continue
                depth -= 1
                if depth == 0:
                    return i
            i += 1
        return -1

    # ------------------------------------------------------------------
    # Classes
    # ------------------------------------------------------------------

    def _extract_classes(self, source: str) -> list[ClassDef]:
        classes: list[ClassDef] = []
        for match in _CLASS_RE.finditer(source):
            bases: list[str] = []
            if match.group("base"):
                bases.append(match.group("base"))
            if match.group("ifaces"):
                bases.extend(i.strip() for i in match.group("ifaces").split(","))

            line_no = source[:match.start()].count("\n") + 1
            class_body = self._extract_brace_block(source, match.end())
            methods = self._extract_methods(class_body, line_no)

            classes.append(ClassDef(
                name=match.group("name"),
                bases=bases,
                methods=methods,
                line_number=line_no,
            ))
        return classes

    def _extract_methods(self, class_body: str, class_start_line: int) -> list[FunctionDef]:
        methods: list[FunctionDef] = []
        for match in _METHOD_RE.finditer(class_body):
            name = match.group("name")
            if name in ("constructor", "if", "for", "while", "switch"):
                if name != "constructor":
                    continue

            access = match.group("access") or "public"
            visibility_map = {
                "public": Visibility.PUBLIC,
                "private": Visibility.PRIVATE,
                "protected": Visibility.PROTECTED,
            }
            params = self._parse_params(match.group("params") or "")

            methods.append(FunctionDef(
                name=name,
                params=params,
                return_type=match.group("return"),
                is_async=bool(match.group("async")),
                is_method=True,
                is_static=bool(match.group("static")),
                visibility=visibility_map.get(access, Visibility.PUBLIC),
                line_number=class_start_line + class_body[:match.start()].count("\n"),
            ))
        return methods

    # ------------------------------------------------------------------
    # Type aliases & interfaces
    # ------------------------------------------------------------------

    def _extract_type_aliases(self, source: str) -> list[TypeAlias]:
        aliases: list[TypeAlias] = []

        for match in _INTERFACE_RE.finditer(source):
            aliases.append(TypeAlias(
                name=match.group("name"),
                definition="interface",
                is_exported=bool(match.group("export")),
                line_number=source[:match.start()].count("\n") + 1,
            ))

        for match in _TYPE_ALIAS_RE.finditer(source):
            aliases.append(TypeAlias(
                name=match.group("name"),
                definition=match.group("def").rstrip(";").strip(),
                is_exported=bool(match.group("export")),
                line_number=source[:match.start()].count("\n") + 1,
            ))

        return aliases

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_params(raw: str) -> list[Parameter]:
        if not raw.strip():
            return []
        params: list[Parameter] = []
        depth = 0
        current = ""
        for ch in raw:
            if ch in "<({":
                depth += 1
                current += ch
            elif ch in ">)}":
                depth -= 1
                current += ch
            elif ch == "," and depth == 0:
                params.append(TypeScriptAnalyzer._make_param(current.strip()))
                current = ""
            else:
                current += ch
        if current.strip():
            params.append(TypeScriptAnalyzer._make_param(current.strip()))
        return params

    @staticmethod
    def _make_param(raw: str) -> Parameter:
        is_optional = "?" in raw
        raw = raw.replace("?", "")

        default = None
        if "=" in raw:
            raw, default = raw.split("=", 1)
            raw = raw.strip()
            default = default.strip()

        annotation = None
        if ":" in raw:
            name_part, annotation = raw.split(":", 1)
            name_part = name_part.strip()
            annotation = annotation.strip()
        else:
            name_part = raw.strip()

        return Parameter(
            name=name_part,
            annotation=annotation,
            default=default,
            is_optional=is_optional or default is not None,
        )

    @staticmethod
    def _extract_brace_block(source: str, start: int) -> str:
        """Return the content between the first ``{`` and its matching ``}``."""
        depth = 0
        begin = None
        for i in range(start, len(source)):
            if source[i] == "{":
                if depth == 0:
                    begin = i + 1
                depth += 1
            elif source[i] == "}":
                depth -= 1
                if depth == 0 and begin is not None:
                    return source[begin:i]
        return ""

    @staticmethod
    def _count_lines(source: str, module: ModuleInfo) -> None:
        for line in source.splitlines():
            stripped = line.strip()
            if not stripped:
                module.blank_lines += 1
            elif stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
                module.comment_lines += 1
            else:
                module.lines_of_code += 1
