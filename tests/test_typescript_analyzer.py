"""Tests for the TypeScript regex-based analyzer."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.analyzer.typescript_analyzer import TypeScriptAnalyzer
from src.models.code_elements import Visibility


@pytest.fixture
def analyzer() -> TypeScriptAnalyzer:
    return TypeScriptAnalyzer()


class TestImportExtraction:
    def test_extracts_named_imports(self, analyzer: TypeScriptAnalyzer, ts_index_path: Path) -> None:
        module = analyzer.analyze_file(ts_index_path)
        import_names = [n for imp in module.imports for n in imp.names]
        assert "User" in import_names
        assert "UserRole" in import_names

    def test_extracts_import_modules(self, analyzer: TypeScriptAnalyzer, ts_index_path: Path) -> None:
        module = analyzer.analyze_file(ts_index_path)
        modules = [imp.module for imp in module.imports]
        assert "./types" in modules
        assert "./utils" in modules


class TestFunctionExtraction:
    def test_extracts_exported_functions(self, analyzer: TypeScriptAnalyzer, ts_index_path: Path) -> None:
        module = analyzer.analyze_file(ts_index_path)
        fn_names = [f.name for f in module.functions]
        assert "initializeApp" in fn_names
        assert "healthCheck" in fn_names

    def test_exported_are_public(self, analyzer: TypeScriptAnalyzer, ts_index_path: Path) -> None:
        module = analyzer.analyze_file(ts_index_path)
        init_fn = next(f for f in module.functions if f.name == "initializeApp")
        assert init_fn.visibility == Visibility.PUBLIC

    def test_async_detection(self, analyzer: TypeScriptAnalyzer, ts_index_path: Path) -> None:
        module = analyzer.analyze_file(ts_index_path)
        init_fn = next(f for f in module.functions if f.name == "initializeApp")
        assert init_fn.is_async is True
        health_fn = next(f for f in module.functions if f.name == "healthCheck")
        assert health_fn.is_async is False

    def test_extracts_params(self, analyzer: TypeScriptAnalyzer, ts_utils_path: Path) -> None:
        module = analyzer.analyze_file(ts_utils_path)
        fmt_fn = next(f for f in module.functions if f.name == "formatDate")
        param_names = [p.name for p in fmt_fn.params]
        assert "date" in param_names
        assert "locale" in param_names

    def test_extracts_arrow_functions(self, analyzer: TypeScriptAnalyzer, ts_utils_path: Path) -> None:
        module = analyzer.analyze_file(ts_utils_path)
        fn_names = [f.name for f in module.functions]
        assert "debounce" in fn_names


class TestClassExtraction:
    def test_extracts_classes(self, analyzer: TypeScriptAnalyzer, ts_index_path: Path) -> None:
        module = analyzer.analyze_file(ts_index_path)
        class_names = [c.name for c in module.classes]
        assert "UserService" in class_names

    def test_extracts_class_methods(self, analyzer: TypeScriptAnalyzer, ts_index_path: Path) -> None:
        module = analyzer.analyze_file(ts_index_path)
        svc = next(c for c in module.classes if c.name == "UserService")
        method_names = [m.name for m in svc.methods]
        assert "getUser" in method_names
        assert "createUser" in method_names
        assert "deleteUser" in method_names
        assert "listUsers" in method_names

    def test_method_async(self, analyzer: TypeScriptAnalyzer, ts_index_path: Path) -> None:
        module = analyzer.analyze_file(ts_index_path)
        svc = next(c for c in module.classes if c.name == "UserService")
        get_user = next(m for m in svc.methods if m.name == "getUser")
        assert get_user.is_async is True
        list_users = next(m for m in svc.methods if m.name == "listUsers")
        assert list_users.is_async is False


class TestTypeAliases:
    def test_extracts_interfaces(self, analyzer: TypeScriptAnalyzer, ts_types_path: Path) -> None:
        module = analyzer.analyze_file(ts_types_path)
        alias_names = [a.name for a in module.type_aliases]
        assert "User" in alias_names
        assert "ApiResponse" in alias_names

    def test_extracts_type_aliases(self, analyzer: TypeScriptAnalyzer, ts_types_path: Path) -> None:
        module = analyzer.analyze_file(ts_types_path)
        alias_names = [a.name for a in module.type_aliases]
        assert "UserRole" in alias_names
        assert "PaginationParams" in alias_names

    def test_exported_flag(self, analyzer: TypeScriptAnalyzer, ts_types_path: Path) -> None:
        module = analyzer.analyze_file(ts_types_path)
        for alias in module.type_aliases:
            assert alias.is_exported is True


class TestLineCounting:
    def test_counts_lines(self, analyzer: TypeScriptAnalyzer, ts_index_path: Path) -> None:
        module = analyzer.analyze_file(ts_index_path)
        assert module.lines_of_code > 0
        assert module.total_lines > 0

    def test_language_is_typescript(self, analyzer: TypeScriptAnalyzer, ts_index_path: Path) -> None:
        module = analyzer.analyze_file(ts_index_path)
        assert module.language == "typescript"
