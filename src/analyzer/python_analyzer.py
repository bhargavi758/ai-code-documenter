"""Python source file analyzer built on the stdlib ``ast`` module."""

from __future__ import annotations

import ast
from pathlib import Path

from src.analyzer.base import BaseAnalyzer
from src.models.code_elements import (
    ClassDef,
    FunctionDef,
    ImportInfo,
    ModuleInfo,
    Parameter,
    Visibility,
)


class PythonAnalyzer(BaseAnalyzer):
    SUPPORTED_EXTENSIONS = (".py",)

    def analyze_file(self, filepath: Path) -> ModuleInfo:
        source = filepath.read_text(encoding="utf-8")
        module = ModuleInfo(filepath=filepath, language="python")
        self._count_lines(source, module)

        try:
            tree = ast.parse(source, filename=str(filepath))
        except SyntaxError as exc:
            module.errors.append(f"SyntaxError: {exc.msg} (line {exc.lineno})")
            return module

        module.docstring = ast.get_docstring(tree)
        module.imports = self._extract_imports(tree)
        module.classes = [self._extract_class(node) for node in ast.iter_child_nodes(tree) if isinstance(node, ast.ClassDef)]
        module.functions = [self._extract_function(node) for node in ast.iter_child_nodes(tree) if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)]

        return module

    # ------------------------------------------------------------------
    # Import extraction
    # ------------------------------------------------------------------

    def _extract_imports(self, tree: ast.Module) -> list[ImportInfo]:
        imports: list[ImportInfo] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(ImportInfo(
                        module=alias.name,
                        alias=alias.asname,
                        is_from_import=False,
                        line_number=node.lineno,
                    ))
            elif isinstance(node, ast.ImportFrom):
                module_name = node.module or ""
                names = [alias.name for alias in node.names]
                imports.append(ImportInfo(
                    module=module_name,
                    names=names,
                    is_from_import=True,
                    line_number=node.lineno,
                ))
        return imports

    # ------------------------------------------------------------------
    # Class extraction
    # ------------------------------------------------------------------

    def _extract_class(self, node: ast.ClassDef) -> ClassDef:
        bases = [self._unparse_node(b) for b in node.bases]
        decorators = [self._unparse_node(d) for d in node.decorator_list]
        is_abstract = any("ABC" in b or "Abstract" in b for b in bases)

        methods: list[FunctionDef] = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
                func = self._extract_function(item, is_method=True)
                methods.append(func)

        return ClassDef(
            name=node.name,
            bases=bases,
            methods=methods,
            docstring=ast.get_docstring(node),
            decorators=decorators,
            is_abstract=is_abstract,
            line_number=node.lineno,
            end_line_number=node.end_lineno or node.lineno,
        )

    # ------------------------------------------------------------------
    # Function / method extraction
    # ------------------------------------------------------------------

    def _extract_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        *,
        is_method: bool = False,
    ) -> FunctionDef:
        params = self._extract_parameters(node.args, is_method=is_method)
        return_type = self._unparse_node(node.returns) if node.returns else None
        decorators = [self._unparse_node(d) for d in node.decorator_list]

        visibility = self._infer_visibility(node.name)
        is_static = "staticmethod" in decorators
        is_classmethod = "classmethod" in decorators
        is_property = "property" in decorators

        from src.metrics.complexity import CyclomaticComplexityCalculator
        complexity = CyclomaticComplexityCalculator.for_node(node)

        return FunctionDef(
            name=node.name,
            params=params,
            return_type=return_type,
            docstring=ast.get_docstring(node),
            decorators=decorators,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            is_method=is_method,
            is_static=is_static,
            is_classmethod=is_classmethod,
            is_property=is_property,
            visibility=visibility,
            line_number=node.lineno,
            end_line_number=node.end_lineno or node.lineno,
            complexity=complexity,
        )

    def _extract_parameters(self, args: ast.arguments, *, is_method: bool) -> list[Parameter]:
        params: list[Parameter] = []
        all_args = args.posonlyargs + args.args + args.kwonlyargs

        num_defaults_offset = len(all_args) - len(args.defaults)
        defaults_padded: list[ast.expr | None] = [None] * num_defaults_offset + list(args.defaults)

        for i, arg in enumerate(all_args):
            if is_method and i == 0 and arg.arg in ("self", "cls"):
                continue
            annotation = self._unparse_node(arg.annotation) if arg.annotation else None
            default = self._unparse_node(defaults_padded[i]) if i < len(defaults_padded) and defaults_padded[i] else None
            params.append(Parameter(
                name=arg.arg,
                annotation=annotation,
                default=default,
                is_optional=default is not None,
            ))

        if args.vararg:
            annotation = self._unparse_node(args.vararg.annotation) if args.vararg.annotation else None
            params.append(Parameter(name=f"*{args.vararg.arg}", annotation=annotation))
        if args.kwarg:
            annotation = self._unparse_node(args.kwarg.annotation) if args.kwarg.annotation else None
            params.append(Parameter(name=f"**{args.kwarg.arg}", annotation=annotation))

        return params

    # ------------------------------------------------------------------
    # Line counting
    # ------------------------------------------------------------------

    @staticmethod
    def _count_lines(source: str, module: ModuleInfo) -> None:
        for line in source.splitlines():
            stripped = line.strip()
            if not stripped:
                module.blank_lines += 1
            elif stripped.startswith("#"):
                module.comment_lines += 1
            else:
                module.lines_of_code += 1

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _unparse_node(node: ast.expr | None) -> str:
        if node is None:
            return ""
        return ast.unparse(node)

    @staticmethod
    def _infer_visibility(name: str) -> Visibility:
        if name.startswith("__") and name.endswith("__"):
            return Visibility.PUBLIC
        if name.startswith("__"):
            return Visibility.PRIVATE
        if name.startswith("_"):
            return Visibility.PROTECTED
        return Visibility.PUBLIC
