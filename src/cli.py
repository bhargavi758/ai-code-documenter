"""Click-based CLI entry point for the AI Code Documenter."""

from __future__ import annotations

import json
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.analyzer.factory import create_analyzer
from src.dependency.graph import DependencyGraph
from src.generators.api_docs_generator import ApiDocsGenerator
from src.generators.json_generator import JsonGenerator
from src.generators.readme_generator import ReadmeGenerator
from src.metrics.statistics import CodeStatistics
from src.models.code_elements import ModuleInfo, ProjectInfo
from src.utils.file_discovery import discover_files

console = Console()


# ------------------------------------------------------------------
# Shared helper: scan a project directory into a ProjectInfo
# ------------------------------------------------------------------

def _build_project(path: str) -> ProjectInfo:
    root = Path(path).resolve()
    if not root.exists():
        raise click.BadParameter(f"Path does not exist: {root}")

    name = root.name
    description = ""
    version = ""

    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        _parse_pyproject_meta(pyproject, locals())

    package_json = root / "package.json"
    if package_json.exists():
        _parse_package_json(package_json, locals())

    files = discover_files(root)
    modules: list[ModuleInfo] = []

    with console.status("[bold green]Analyzing files…") as status:
        for filepath in files:
            analyzer = create_analyzer(filepath)
            if analyzer is None:
                continue
            status.update(f"[bold green]Analyzing [cyan]{filepath.name}")
            module = analyzer.analyze_file(filepath)
            modules.append(module)

    return ProjectInfo(
        root=root,
        name=name,
        description=description,
        version=version,
        modules=modules,
    )


def _parse_pyproject_meta(pyproject: Path, ns: dict) -> None:
    """Best-effort extraction of name/description/version from pyproject.toml."""
    try:
        text = pyproject.read_text(encoding="utf-8")
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("name") and "=" in stripped:
                ns["name"] = stripped.split("=", 1)[1].strip().strip('"').strip("'")
            elif stripped.startswith("description") and "=" in stripped:
                ns["description"] = stripped.split("=", 1)[1].strip().strip('"').strip("'")
            elif stripped.startswith("version") and "=" in stripped:
                ns["version"] = stripped.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass


def _parse_package_json(package_json: Path, ns: dict) -> None:
    try:
        data = json.loads(package_json.read_text(encoding="utf-8"))
        ns["name"] = data.get("name", ns.get("name", ""))
        ns["description"] = data.get("description", ns.get("description", ""))
        ns["version"] = data.get("version", ns.get("version", ""))
    except (OSError, json.JSONDecodeError):
        pass


# ------------------------------------------------------------------
# CLI group
# ------------------------------------------------------------------

@click.group()
@click.version_option(version="1.0.0", prog_name="docgen")
def main() -> None:
    """AI Code Documenter — auto-generate documentation from source code."""


# ------------------------------------------------------------------
# analyze
# ------------------------------------------------------------------

@main.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("-o", "--output", default="docs", help="Output directory for generated docs.")
@click.option("-f", "--format", "fmt", type=click.Choice(["markdown", "json"]), default="markdown", help="Output format.")
def analyze(path: str, output: str, fmt: str) -> None:
    """Generate full documentation for a project."""
    project = _build_project(path)
    out_dir = Path(output)
    out_dir.mkdir(parents=True, exist_ok=True)

    if fmt == "json":
        generator = JsonGenerator()
        dest = out_dir / "api.json"
        generator.write(project, dest)
        console.print(f"[green]✓[/green] JSON docs written to {dest}")
    else:
        readme_gen = ReadmeGenerator()
        readme_dest = out_dir / "README.md"
        readme_gen.write(project, readme_dest)

        api_gen = ApiDocsGenerator()
        api_dest = out_dir / "API.md"
        api_gen.write(project, api_dest)

        dep_graph = DependencyGraph.from_project(project)
        dep_dest = out_dir / "DEPENDENCIES.md"
        dep_dest.write_text(dep_graph.to_markdown(), encoding="utf-8")

        console.print(f"[green]✓[/green] README  → {readme_dest}")
        console.print(f"[green]✓[/green] API     → {api_dest}")
        console.print(f"[green]✓[/green] Deps    → {dep_dest}")

    _print_summary(project)


# ------------------------------------------------------------------
# readme
# ------------------------------------------------------------------

@main.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("-o", "--output", default="README.md", help="Output file path.")
def readme(path: str, output: str) -> None:
    """Generate a README for a project."""
    project = _build_project(path)
    dest = Path(output)
    ReadmeGenerator().write(project, dest)
    console.print(f"[green]✓[/green] README written to {dest}")
    _print_summary(project)


# ------------------------------------------------------------------
# stats
# ------------------------------------------------------------------

@main.command()
@click.argument("path", type=click.Path(exists=True))
def stats(path: str) -> None:
    """Show project statistics."""
    project = _build_project(path)
    statistics = CodeStatistics.from_project(project)

    table = Table(title="Project Statistics", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")

    table.add_row("Files", str(statistics.total_files))
    table.add_row("Languages", ", ".join(sorted(statistics.languages or set())))
    table.add_row("Lines (total)", str(statistics.total_lines))
    table.add_row("  Code", str(statistics.code_lines))
    table.add_row("  Comments", str(statistics.comment_lines))
    table.add_row("  Blank", str(statistics.blank_lines))
    table.add_row("Classes", str(statistics.total_classes))
    table.add_row("Functions", str(statistics.total_functions))
    table.add_row("Methods", str(statistics.total_methods))
    table.add_row("Avg Complexity", str(statistics.average_complexity))
    table.add_row("Max Complexity", f"{statistics.max_complexity} ({statistics.max_complexity_function})")

    console.print(table)


# ------------------------------------------------------------------
# deps
# ------------------------------------------------------------------

@main.command()
@click.argument("path", type=click.Path(exists=True))
def deps(path: str) -> None:
    """Show dependency graph as Markdown."""
    project = _build_project(path)
    graph = DependencyGraph.from_project(project)
    console.print(graph.to_markdown())


# ------------------------------------------------------------------
# check
# ------------------------------------------------------------------

@main.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("-d", "--docs", default="docs", help="Path to existing docs directory.")
def check(path: str, docs: str) -> None:
    """Check for stale documentation by comparing code state to existing docs."""
    project = _build_project(path)
    docs_dir = Path(docs)

    if not docs_dir.exists():
        console.print(f"[yellow]⚠[/yellow]  Docs directory '{docs_dir}' does not exist. Run [bold]docgen analyze[/bold] first.")
        return

    fresh_readme = ReadmeGenerator().generate(project)
    existing_readme = docs_dir / "README.md"

    if existing_readme.exists():
        existing_text = existing_readme.read_text(encoding="utf-8")
        if existing_text.strip() == fresh_readme.strip():
            console.print("[green]✓[/green] README is up to date.")
        else:
            console.print("[yellow]⚠[/yellow]  README is [bold]stale[/bold] — code has changed since docs were generated.")
    else:
        console.print("[yellow]⚠[/yellow]  No README.md found in docs directory.")

    fresh_api = ApiDocsGenerator().generate(project)
    existing_api = docs_dir / "API.md"
    if existing_api.exists():
        existing_api_text = existing_api.read_text(encoding="utf-8")
        if existing_api_text.strip() == fresh_api.strip():
            console.print("[green]✓[/green] API docs are up to date.")
        else:
            console.print("[yellow]⚠[/yellow]  API docs are [bold]stale[/bold] — code has changed since docs were generated.")
    else:
        console.print("[yellow]⚠[/yellow]  No API.md found in docs directory.")


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _print_summary(project: ProjectInfo) -> None:
    summary = (
        f"[bold]{project.name}[/bold]: "
        f"{project.total_files} files, "
        f"{project.total_classes} classes, "
        f"{project.total_functions} functions, "
        f"{project.total_lines} lines"
    )
    console.print(Panel(summary, title="Summary", border_style="blue"))


if __name__ == "__main__":
    main()
