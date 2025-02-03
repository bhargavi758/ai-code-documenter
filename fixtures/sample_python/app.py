"""Main application module for the sample project.

Provides the core ``Application`` class and a convenience ``run`` helper.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from models import User, UserRole
from utils import slugify, validate_email

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Runtime configuration loaded from environment or file."""

    debug: bool = False
    port: int = 8000
    allowed_origins: list[str] = field(default_factory=lambda: ["*"])


class Application:
    """HTTP application container with middleware support."""

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config()
        self._middleware: list[Any] = []
        self._routes: dict[str, Any] = {}

    def use(self, middleware: Any) -> None:
        """Register a middleware function."""
        self._middleware.append(middleware)

    def route(self, path: str, handler: Any) -> None:
        """Bind *handler* to *path*."""
        if path in self._routes:
            logger.warning("Overwriting existing route: %s", path)
        self._routes[path] = handler

    async def handle_request(self, path: str, **kwargs: Any) -> dict[str, Any]:
        """Dispatch an incoming request through the middleware chain."""
        handler = self._routes.get(path)
        if handler is None:
            return {"status": 404, "body": "Not Found"}

        context: dict[str, Any] = {"path": path, **kwargs}
        for mw in self._middleware:
            context = mw(context)

        try:
            result = await handler(context)
            return {"status": 200, "body": result}
        except PermissionError:
            return {"status": 403, "body": "Forbidden"}
        except Exception as exc:
            logger.exception("Unhandled error on %s", path)
            return {"status": 500, "body": str(exc)}

    @property
    def route_count(self) -> int:
        return len(self._routes)


def create_app(*, debug: bool = False) -> Application:
    """Factory function that creates a fully configured application."""
    config = Config(debug=debug)
    app = Application(config)
    return app


def run(app: Application, port: int | None = None) -> None:
    """Start serving the application (placeholder)."""
    effective_port = port or app.config.port
    logger.info("Serving on port %d", effective_port)
