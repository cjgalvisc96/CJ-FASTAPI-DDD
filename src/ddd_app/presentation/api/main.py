"""ASGI entrypoint + `ddd-api` console script."""

from __future__ import annotations

import os

from ddd_app.core.config import get_settings
from ddd_app.core.di.container import build_container
from ddd_app.core.logging import configure_logging
from ddd_app.presentation.api.app import create_app

settings = get_settings()
configure_logging(settings.log_level)
container = build_container(settings)
app = create_app(settings=settings, container=container)


def main() -> None:
    import uvicorn

    reload = os.environ.get("API_RELOAD", "").lower() in {"1", "true", "yes", "on"}
    uvicorn.run(
        "ddd_app.presentation.api.main:app",
        # Bind all interfaces: required to be reachable inside a container / Lambda.
        host="0.0.0.0",  # noqa: S104  # nosec B104
        port=int(os.environ.get("API_PORT", "8000")),
        reload=reload,
        reload_dirs=["src"] if reload else None,
    )
