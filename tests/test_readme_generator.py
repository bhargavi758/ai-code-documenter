"""Tests for the README generator."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.analyzer.python_analyzer import PythonAnalyzer
from src.generators.readme_generator import ReadmeGenerator
from src.models.code_elements import ProjectInfo


@pytest.fixture
def project(sample_python_dir: Path) -> ProjectInfo:
    analyzer = PythonAnalyzer()
    modules = []
    for f in sorted(sample_python_dir.glob("*.py")):
        modules.append(analyzer.analyze_file(f))
    return ProjectInfo(
        root=sample_python_dir,
        name="sample-project",
        description="A sample project for testing",
        version="0.1.0",
        modules=modules,
    )


@pytest.fixture
def generator() -> ReadmeGenerator:
    return ReadmeGenerator()


class TestReadmeGeneration:
    def test_contains_project_name(self, generator: ReadmeGenerator, project: ProjectInfo) -> None:
        output = generator.generate(project)
        assert "# sample-project" in output

    def test_contains_description(self, generator: ReadmeGenerator, project: ProjectInfo) -> None:
        output = generator.generate(project)
        assert "A sample project for testing" in output

    def test_contains_table_of_contents(self, generator: ReadmeGenerator, project: ProjectInfo) -> None:
        output = generator.generate(project)
        assert "Table of Contents" in output
        assert "[Overview]" in output

    def test_contains_statistics_table(self, generator: ReadmeGenerator, project: ProjectInfo) -> None:
        output = generator.generate(project)
        assert "| Metric | Value |" in output

    def test_lists_classes(self, generator: ReadmeGenerator, project: ProjectInfo) -> None:
        output = generator.generate(project)
        assert "Application" in output
        assert "User" in output

    def test_lists_functions(self, generator: ReadmeGenerator, project: ProjectInfo) -> None:
        output = generator.generate(project)
        assert "create_app" in output
        assert "slugify" in output

    def test_contains_installation(self, generator: ReadmeGenerator, project: ProjectInfo) -> None:
        output = generator.generate(project)
        assert "Installation" in output
        assert "pip install" in output

    def test_write_creates_file(self, generator: ReadmeGenerator, project: ProjectInfo, tmp_path: Path) -> None:
        dest = tmp_path / "README.md"
        generator.write(project, dest)
        assert dest.exists()
        content = dest.read_text()
        assert "sample-project" in content
