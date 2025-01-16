"""Walk a directory tree and yield source files matching supported extensions."""

from __future__ import annotations

from pathlib import Path

from src.analyzer.factory import SUPPORTED_EXTENSIONS

DEFAULT_IGNORE_DIRS = frozenset({
    "__pycache__",
    ".git",
    ".svn",
    "node_modules",
    ".venv",
    "venv",
    "env",
    ".mypy_cache",
    ".pytest_cache",
    ".tox",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "coverage",
})


def discover_files(
    root: Path,
    *,
    extensions: set[str] | None = None,
    ignore_dirs: frozenset[str] = DEFAULT_IGNORE_DIRS,
) -> list[Path]:
    """Recursively find source files under *root*.

    Returns a sorted list of paths matching *extensions* (defaults to
    all analyzer-supported extensions).
    """
    if extensions is None:
        extensions = SUPPORTED_EXTENSIONS

    root = root.resolve()
    if not root.is_dir():
        if root.is_file() and root.suffix in extensions:
            return [root]
        return []

    found: list[Path] = []
    for path in root.rglob("*"):
        if any(part in ignore_dirs for part in path.parts):
            continue
        if path.is_file() and path.suffix in extensions:
            found.append(path)

    return sorted(found)
