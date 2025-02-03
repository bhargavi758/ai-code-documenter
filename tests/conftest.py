"""Shared fixtures for the test suite."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"
SAMPLE_PYTHON_DIR = FIXTURES_DIR / "sample_python"
SAMPLE_TS_DIR = FIXTURES_DIR / "sample_typescript"


@pytest.fixture
def sample_python_dir() -> Path:
    return SAMPLE_PYTHON_DIR


@pytest.fixture
def sample_ts_dir() -> Path:
    return SAMPLE_TS_DIR


@pytest.fixture
def python_app_path() -> Path:
    return SAMPLE_PYTHON_DIR / "app.py"


@pytest.fixture
def python_models_path() -> Path:
    return SAMPLE_PYTHON_DIR / "models.py"


@pytest.fixture
def python_utils_path() -> Path:
    return SAMPLE_PYTHON_DIR / "utils.py"


@pytest.fixture
def ts_index_path() -> Path:
    return SAMPLE_TS_DIR / "index.ts"


@pytest.fixture
def ts_types_path() -> Path:
    return SAMPLE_TS_DIR / "types.ts"


@pytest.fixture
def ts_utils_path() -> Path:
    return SAMPLE_TS_DIR / "utils.ts"


@pytest.fixture
def trivial_python_source(tmp_path: Path) -> Path:
    """A minimal Python file for quick tests."""
    p = tmp_path / "trivial.py"
    p.write_text(
        'def greet(name: str) -> str:\n'
        '    """Return a greeting."""\n'
        '    return f"Hello, {name}!"\n',
        encoding="utf-8",
    )
    return p


@pytest.fixture
def trivial_ts_source(tmp_path: Path) -> Path:
    p = tmp_path / "trivial.ts"
    p.write_text(
        'export function greet(name: string): string {\n'
        '  return `Hello, ${name}!`;\n'
        '}\n',
        encoding="utf-8",
    )
    return p
