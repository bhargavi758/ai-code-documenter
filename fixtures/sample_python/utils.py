"""Shared utility functions."""

from __future__ import annotations

import re
import unicodedata


def slugify(text: str, *, max_length: int = 80) -> str:
    """Convert *text* to a URL-safe slug.

    Normalises Unicode, strips non-alphanumeric characters, collapses
    dashes, and truncates to *max_length*.
    """
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[-\s]+", "-", text).strip("-")
    return text[:max_length]


def validate_email(email: str) -> bool:
    """Return True if *email* looks like a valid email address."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def chunk_list(items: list, size: int) -> list[list]:
    """Split *items* into sublists of at most *size* elements."""
    if size <= 0:
        raise ValueError("Chunk size must be positive")
    return [items[i : i + size] for i in range(0, len(items), size)]


def deep_merge(base: dict, overrides: dict) -> dict:
    """Recursively merge *overrides* into *base*, returning a new dict."""
    result = base.copy()
    for key, value in overrides.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result
