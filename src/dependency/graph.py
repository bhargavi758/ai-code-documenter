"""Builds a dependency graph from import statements across modules."""

from __future__ import annotations

from collections import defaultdict

from src.models.code_elements import ProjectInfo
from src.utils.formatting import MarkdownFormatter as Fmt


class DependencyGraph:
    """Maps each module to its inbound and outbound import edges."""

    def __init__(self) -> None:
        self.edges: dict[str, set[str]] = defaultdict(set)
        self.reverse_edges: dict[str, set[str]] = defaultdict(set)
        self._module_names: set[str] = set()

    @classmethod
    def from_project(cls, project: ProjectInfo) -> DependencyGraph:
        graph = cls()
        module_stems = {m.name for m in project.modules}
        graph._module_names = module_stems

        for module in project.modules:
            for imp in module.imports:
                target = imp.module.split(".")[0]
                if target in module_stems and target != module.name:
                    graph.edges[module.name].add(target)
                    graph.reverse_edges[target].add(module.name)

        return graph

    @property
    def nodes(self) -> set[str]:
        all_nodes = set(self.edges.keys())
        for targets in self.edges.values():
            all_nodes.update(targets)
        return all_nodes

    def dependents_of(self, module: str) -> set[str]:
        return self.reverse_edges.get(module, set())

    def dependencies_of(self, module: str) -> set[str]:
        return self.edges.get(module, set())

    def has_circular(self) -> list[tuple[str, str]]:
        circular: list[tuple[str, str]] = []
        for source, targets in self.edges.items():
            for target in targets:
                if source in self.edges.get(target, set()):
                    pair = tuple(sorted((source, target)))
                    if pair not in circular:
                        circular.append(pair)  # type: ignore[arg-type]
        return circular

    def to_markdown(self) -> str:
        lines = [Fmt.heading("Dependency Graph", level=2)]

        if not self.edges:
            lines.append("No inter-module dependencies detected.")
            return "\n".join(lines)

        for source in sorted(self.edges):
            targets = sorted(self.edges[source])
            lines.append(f"- **{source}** → {', '.join(f'`{t}`' for t in targets)}")

        circular = self.has_circular()
        if circular:
            lines.append("")
            lines.append(Fmt.heading("Circular Dependencies", level=3))
            for a, b in circular:
                lines.append(f"- `{a}` ↔ `{b}`")

        return "\n".join(lines)

    def to_adjacency_dict(self) -> dict[str, list[str]]:
        return {k: sorted(v) for k, v in self.edges.items()}
