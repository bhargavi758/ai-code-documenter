"""Tests for the dependency graph builder."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.analyzer.python_analyzer import PythonAnalyzer
from src.dependency.graph import DependencyGraph
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
        modules=modules,
    )


class TestDependencyGraph:
    def test_builds_edges(self, project: ProjectInfo) -> None:
        graph = DependencyGraph.from_project(project)
        app_deps = graph.dependencies_of("app")
        assert "models" in app_deps or "utils" in app_deps

    def test_reverse_edges(self, project: ProjectInfo) -> None:
        graph = DependencyGraph.from_project(project)
        if graph.dependencies_of("app"):
            dep = next(iter(graph.dependencies_of("app")))
            assert "app" in graph.dependents_of(dep)

    def test_to_markdown_contains_heading(self, project: ProjectInfo) -> None:
        graph = DependencyGraph.from_project(project)
        md = graph.to_markdown()
        assert "## Dependency Graph" in md

    def test_to_adjacency_dict(self, project: ProjectInfo) -> None:
        graph = DependencyGraph.from_project(project)
        adj = graph.to_adjacency_dict()
        assert isinstance(adj, dict)
        for key, val in adj.items():
            assert isinstance(key, str)
            assert isinstance(val, list)

    def test_empty_project(self) -> None:
        project = ProjectInfo(root=Path("/tmp"), name="empty", modules=[])
        graph = DependencyGraph.from_project(project)
        assert len(graph.edges) == 0
        md = graph.to_markdown()
        assert "No inter-module dependencies" in md

    def test_circular_detection(self, project: ProjectInfo) -> None:
        graph = DependencyGraph.from_project(project)
        circular = graph.has_circular()
        assert isinstance(circular, list)
