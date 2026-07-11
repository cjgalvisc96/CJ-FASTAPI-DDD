"""Shared test fixtures: a SQLite-backed DI container with an in-process fake Redis.

The whole suite runs with **no external services** — SQLite stands in for Postgres, an in-process
fake stands in for Redis (cache + rate limiter + health check), and Keycloak is faked per-test. So
tests never touch localhost:5432/6379/8080, even when another project's stack is running there.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from dependency_injector import providers

from ddd_app.contexts.shared.infrastructure.db.registry import Base
from ddd_app.core.di.container import ApplicationContainer

_SQLITE_CONFIG = {
    "db_echo": False,
    "db_pool_size": 5,
    "db_pool_max_overflow": 10,
    "redis_dsn": "redis://localhost:6379/0",  # unused — the redis provider is overridden below
    "cache_enable": False,
    "cache_namespace_list": ["users"],
    "keycloak_verify_audience": False,
    "oidc_issuer_effective": "http://localhost:8080/realms/ddd",
    "oidc_jwks_url_effective": "http://localhost:8080/realms/ddd/protocol/openid-connect/certs",
    "oidc_client_id_effective": "ddd-api",
}


class FakeRedis:
    """In-process async stand-in for redis.asyncio.Redis (cache + rate-limit + health)."""

    def __init__(self) -> None:
        self._store: dict[str, str | int] = {}

    async def get(self, key: str):
        return self._store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self._store[key] = value

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def incr(self, key: str) -> int:
        value = int(self._store.get(key, 0)) + 1
        self._store[key] = value
        return value

    async def expire(self, key: str, seconds: int) -> bool:
        return True

    async def ping(self) -> bool:
        return True

    async def aclose(self) -> None:
        return None


@pytest.fixture
async def container(tmp_path) -> AsyncIterator[ApplicationContainer]:
    dsn = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    c = ApplicationContainer()
    c.config.from_dict({**_SQLITE_CONFIG, "database_dsn": dsn})
    # Isolate Redis: cache, rate-limit middleware, and /health all use this fake — no network.
    c.shared.redis.override(providers.Object(FakeRedis()))
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
