from __future__ import annotations

from pydantic import BaseModel

from ddd_app.contexts.shared.infrastructure.cache.redis_cache import RedisCache
from ddd_app.presentation.api.caching import cached


class _Model(BaseModel):
    value: int


class FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    async def get(self, key: str):
        return self.store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.store[key] = value

    async def delete(self, key: str) -> None:
        self.store.pop(key, None)


async def test_cached_miss_then_hit() -> None:
    cache = RedisCache(FakeRedis(), enabled=True, namespaces=["users"])  # type: ignore[arg-type]
    calls = {"n": 0}

    async def produce() -> _Model:
        calls["n"] += 1
        return _Model(value=42)

    first = await cached(cache, "users", "k", _Model, produce)
    assert first.value == 42
    assert calls["n"] == 1

    # Second call is served from cache — produce() is NOT invoked again.
    second = await cached(cache, "users", "k", _Model, produce)
    assert second.value == 42
    assert calls["n"] == 1


async def test_cached_disabled_always_produces() -> None:
    cache = RedisCache(FakeRedis(), enabled=False, namespaces=["users"])  # type: ignore[arg-type]
    calls = {"n": 0}

    async def produce() -> _Model:
        calls["n"] += 1
        return _Model(value=1)

    await cached(cache, "users", "k", _Model, produce)
    await cached(cache, "users", "k", _Model, produce)
    assert calls["n"] == 2
