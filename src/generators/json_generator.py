"""Serializes the full project analysis to JSON for machine consumption."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from src.generators.base import BaseGenerator
from src.models.code_elements import ProjectInfo


def _default_serializer(obj: Any) -> Any:
    if isinstance(obj, Path):
        return str(obj)
    if hasattr(obj, "value"):
        return obj.value
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


class JsonGenerator(BaseGenerator):
    def __init__(self, *, indent: int = 2) -> None:
        self._indent = indent

    def generate(self, project: ProjectInfo) -> str:
        data = asdict(project)
        return json.dumps(data, default=_default_serializer, indent=self._indent)
