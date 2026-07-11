from __future__ import annotations

import pytest

from ddd_app.contexts.shared.infrastructure.cache.redis_cache import RedisCache


class FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    async def get(self, key: str):
        return self.store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.store[key] = value

    async def delete(self, key: str) -> None:
        self.store.pop(key, None)

    async def ping(self) -> None:
        return None

    async def aclose(self) -> None:
        return None


async def test_disabled_cache_is_noop() -> None:
    cache = RedisCache(FakeRedis(), enabled=False, namespaces=["users"])  # type: ignore[arg-type]
    await cache.set("users", "k", "v")
    assert await cache.get("users", "k") is None


async def test_enabled_cache_roundtrip() -> None:
    cache = RedisCache(FakeRedis(), enabled=True, namespaces=["users"])  # type: ignore[arg-type]
    await cache.set("users", "k", "v")
    assert await cache.get("users", "k") == "v"
    await cache.invalidate("users", "k")
    assert await cache.get("users", "k") is None


async def test_unknown_namespace_rejected() -> None:
    cache = RedisCache(FakeRedis(), enabled=True, namespaces=["users"])  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        await cache.get("tasks", "k")
