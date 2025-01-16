"""Markdown formatting helpers used by generators."""

from __future__ import annotations


class MarkdownFormatter:
    @staticmethod
    def heading(text: str, level: int = 1) -> str:
        prefix = "#" * min(max(level, 1), 6)
        return f"{prefix} {text}"

    @staticmethod
    def code_block(code: str, language: str = "") -> str:
        return f"```{language}\n{code}\n```"

    @staticmethod
    def table(headers: list[str], rows: list[tuple[str, ...]]) -> str:
        header_line = "| " + " | ".join(headers) + " |"
        separator = "| " + " | ".join("---" for _ in headers) + " |"
        body_lines = ["| " + " | ".join(row) + " |" for row in rows]
        return "\n".join([header_line, separator, *body_lines])

    @staticmethod
    def bold(text: str) -> str:
        return f"**{text}**"

    @staticmethod
    def inline_code(text: str) -> str:
        return f"`{text}`"

    @staticmethod
    def link(text: str, url: str) -> str:
        return f"[{text}]({url})"

    @staticmethod
    def unordered_list(items: list[str]) -> str:
        return "\n".join(f"- {item}" for item in items)
