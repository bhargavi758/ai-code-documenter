"""Domain models for the sample project."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class UserRole(Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


@dataclass
class User:
    """A registered user in the system."""

    id: int
    username: str
    email: str
    role: UserRole = UserRole.VIEWER
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    def promote(self, new_role: UserRole) -> None:
        """Promote user to a higher role."""
        if new_role.value == "admin" and not self.is_active:
            raise ValueError("Cannot promote inactive user to admin")
        self.role = new_role

    def deactivate(self) -> None:
        self.is_active = False


@dataclass
class Article:
    """Content article authored by a user."""

    id: int
    title: str
    body: str
    author: User
    published: bool = False
    tags: list[str] = field(default_factory=list)

    @property
    def summary(self) -> str:
        return self.body[:140] + "…" if len(self.body) > 140 else self.body

    def publish(self) -> None:
        if not self.author.is_active:
            raise PermissionError("Inactive authors cannot publish")
        self.published = True

    def add_tag(self, tag: str) -> None:
        normalized = tag.lower().strip()
        if normalized and normalized not in self.tags:
            self.tags.append(normalized)
