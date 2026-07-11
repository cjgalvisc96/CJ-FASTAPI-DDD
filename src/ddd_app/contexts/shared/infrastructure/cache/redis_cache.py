"""Namespace-aware async Redis cache.

Keys are stored as ``<namespace>:<key>``. Namespaces are validated against an allow-list (from the
``CACHE_NAMESPACES`` setting) so a typo can't silently write to an unmanaged keyspace. When
disabled, every op is a no-op and ``get`` returns ``None`` — so caching can be turned off globally.
"""

from __future__ import annotations

from collections.abc import Iterable

from redis.asyncio import Redis


class RedisCache:
    def __init__(
        self,
        redis: Redis,
        *,
        enabled: bool = True,
        namespaces: Iterable[str] = (),
    ) -> None:
        self._redis = redis
        self._enabled = enabled
        self._namespaces = set(namespaces)

    def _key(self, namespace: str, key: str) -> str:
        if self._namespaces and namespace not in self._namespaces:
            raise ValueError(f"Unknown cache namespace: {namespace}")
        return f"{namespace}:{key}"

    async def get(self, namespace: str, key: str) -> str | None:
        if not self._enabled:
            return None
        value = await self._redis.get(self._key(namespace, key))
        return value.decode() if isinstance(value, bytes) else value

    async def set(self, namespace: str, key: str, value: str, *, ttl: int = 300) -> None:
        if not self._enabled:
            return
        await self._redis.set(self._key(namespace, key), value, ex=ttl)

    async def invalidate(self, namespace: str, key: str) -> None:
        if not self._enabled:
            return
        await self._redis.delete(self._key(namespace, key))

    async def ping(self) -> None:
        await self._redis.ping()

    async def close(self) -> None:
        await self._redis.aclose()
