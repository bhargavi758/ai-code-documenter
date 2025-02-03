"""Tests for the Python AST analyzer."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.analyzer.python_analyzer import PythonAnalyzer
from src.models.code_elements import Visibility


@pytest.fixture
def analyzer() -> PythonAnalyzer:
    return PythonAnalyzer()


class TestModuleParsing:
    def test_extracts_module_docstring(self, analyzer: PythonAnalyzer, python_app_path: Path) -> None:
        module = analyzer.analyze_file(python_app_path)
        assert module.docstring is not None
        assert "Main application module" in module.docstring

    def test_language_is_python(self, analyzer: PythonAnalyzer, python_app_path: Path) -> None:
        module = analyzer.analyze_file(python_app_path)
        assert module.language == "python"

    def test_counts_lines(self, analyzer: PythonAnalyzer, python_app_path: Path) -> None:
        module = analyzer.analyze_file(python_app_path)
        assert module.lines_of_code > 0
        assert module.total_lines > module.lines_of_code

    def test_handles_syntax_error(self, analyzer: PythonAnalyzer, tmp_path: Path) -> None:
        bad_file = tmp_path / "bad.py"
        bad_file.write_text("def broken(:\n    pass\n", encoding="utf-8")
        module = analyzer.analyze_file(bad_file)
        assert len(module.errors) > 0
        assert "SyntaxError" in module.errors[0]


class TestImportExtraction:
    def test_extracts_standard_imports(self, analyzer: PythonAnalyzer, python_app_path: Path) -> None:
        module = analyzer.analyze_file(python_app_path)
        import_modules = [imp.module for imp in module.imports]
        assert "logging" in import_modules

    def test_extracts_from_imports(self, analyzer: PythonAnalyzer, python_app_path: Path) -> None:
        module = analyzer.analyze_file(python_app_path)
        from_imports = [imp for imp in module.imports if imp.is_from_import]
        assert len(from_imports) > 0
        dataclass_import = next((imp for imp in from_imports if imp.module == "dataclasses"), None)
        assert dataclass_import is not None
        assert "dataclass" in dataclass_import.names


class TestClassExtraction:
    def test_extracts_classes(self, analyzer: PythonAnalyzer, python_app_path: Path) -> None:
        module = analyzer.analyze_file(python_app_path)
        class_names = [c.name for c in module.classes]
        assert "Application" in class_names
        assert "Config" in class_names

    def test_extracts_class_docstring(self, analyzer: PythonAnalyzer, python_app_path: Path) -> None:
        module = analyzer.analyze_file(python_app_path)
        app_cls = next(c for c in module.classes if c.name == "Application")
        assert app_cls.docstring is not None

    def test_extracts_class_methods(self, analyzer: PythonAnalyzer, python_app_path: Path) -> None:
        module = analyzer.analyze_file(python_app_path)
        app_cls = next(c for c in module.classes if c.name == "Application")
        method_names = [m.name for m in app_cls.methods]
        assert "__init__" in method_names
        assert "handle_request" in method_names

    def test_extracts_decorators(self, analyzer: PythonAnalyzer, python_app_path: Path) -> None:
        module = analyzer.analyze_file(python_app_path)
        app_cls = next(c for c in module.classes if c.name == "Application")
        route_count = next(m for m in app_cls.methods if m.name == "route_count")
        assert "property" in route_count.decorators

    def test_extracts_base_classes(self, analyzer: PythonAnalyzer, python_models_path: Path) -> None:
        module = analyzer.analyze_file(python_models_path)
        role_cls = next((c for c in module.classes if c.name == "UserRole"), None)
        assert role_cls is not None
        assert "Enum" in role_cls.bases


class TestFunctionExtraction:
    def test_extracts_top_level_functions(self, analyzer: PythonAnalyzer, python_app_path: Path) -> None:
        module = analyzer.analyze_file(python_app_path)
        fn_names = [f.name for f in module.functions]
        assert "create_app" in fn_names
        assert "run" in fn_names

    def test_extracts_return_type(self, analyzer: PythonAnalyzer, python_app_path: Path) -> None:
        module = analyzer.analyze_file(python_app_path)
        create_fn = next(f for f in module.functions if f.name == "create_app")
        assert create_fn.return_type == "Application"

    def test_extracts_parameters(self, analyzer: PythonAnalyzer, python_app_path: Path) -> None:
        module = analyzer.analyze_file(python_app_path)
        run_fn = next(f for f in module.functions if f.name == "run")
        param_names = [p.name for p in run_fn.params]
        assert "app" in param_names
        assert "port" in param_names

    def test_extracts_parameter_types(self, analyzer: PythonAnalyzer, python_app_path: Path) -> None:
        module = analyzer.analyze_file(python_app_path)
        run_fn = next(f for f in module.functions if f.name == "run")
        app_param = next(p for p in run_fn.params if p.name == "app")
        assert app_param.annotation == "Application"

    def test_detects_async_functions(self, analyzer: PythonAnalyzer, python_app_path: Path) -> None:
        module = analyzer.analyze_file(python_app_path)
        app_cls = next(c for c in module.classes if c.name == "Application")
        handle = next(m for m in app_cls.methods if m.name == "handle_request")
        assert handle.is_async is True

    def test_function_docstrings(self, analyzer: PythonAnalyzer, python_utils_path: Path) -> None:
        module = analyzer.analyze_file(python_utils_path)
        slugify_fn = next(f for f in module.functions if f.name == "slugify")
        assert slugify_fn.docstring is not None
        assert "URL-safe slug" in slugify_fn.docstring


class TestVisibility:
    def test_public_function(self, analyzer: PythonAnalyzer, trivial_python_source: Path) -> None:
        module = analyzer.analyze_file(trivial_python_source)
        assert module.functions[0].visibility == Visibility.PUBLIC

    def test_private_detected(self, analyzer: PythonAnalyzer, tmp_path: Path) -> None:
        p = tmp_path / "vis.py"
        p.write_text("def _helper(): ...\ndef __mangled(): ...\ndef __init__(self): ...\n")
        module = analyzer.analyze_file(p)
        names_vis = {f.name: f.visibility for f in module.functions}
        assert names_vis["_helper"] == Visibility.PROTECTED
        assert names_vis["__mangled"] == Visibility.PRIVATE
        assert names_vis["__init__"] == Visibility.PUBLIC
