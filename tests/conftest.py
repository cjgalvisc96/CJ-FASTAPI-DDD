"""Shared test fixtures: a SQLite-backed DI container + a request-scoped session."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from ddd_app.contexts.shared.infrastructure.db.registry import Base
from ddd_app.core.di.container import ApplicationContainer

_SQLITE_CONFIG = {
    "db_echo": False,
    "db_pool_size": 5,
    "db_pool_max_overflow": 10,
    "redis_dsn": "redis://localhost:6379/0",
    "cache_enable": False,
    "cache_namespace_list": ["users"],
    "keycloak_url": "http://localhost:8080",
    "keycloak_realm": "ddd",
    "keycloak_client_id": "ddd-api",
    "keycloak_verify_audience": False,
}


@pytest.fixture
async def container(tmp_path) -> AsyncIterator[ApplicationContainer]:
    dsn = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    c = ApplicationContainer()
    c.config.from_dict({**_SQLITE_CONFIG, "database_dsn": dsn})
    database = c.shared.database()
    async with database.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield c
    await database.dispose()


@pytest.fixture
async def session(container: ApplicationContainer):
    """Open a request-scoped session (sets the scoped-session contextvar)."""
    database = container.shared.database()
    async with database.session_scope() as s:
        yield s
