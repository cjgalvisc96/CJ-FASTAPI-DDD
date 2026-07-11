from __future__ import annotations

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from ddd_app.presentation.api.middleware.body_size import MaxBodySizeMiddleware
from ddd_app.presentation.api.middleware.rate_limit import RateLimitMiddleware


class FakeRedis:
    def __init__(self) -> None:
        self.counts: dict[str, int] = {}

    async def incr(self, key: str) -> int:
        self.counts[key] = self.counts.get(key, 0) + 1
        return self.counts[key]

    async def expire(self, key: str, seconds: int) -> bool:
        return True


class BrokenRedis:
    async def incr(self, key: str) -> int:
        raise ConnectionError("redis down")

    async def expire(self, key: str, seconds: int) -> bool:
        raise ConnectionError("redis down")


def _app_with(middleware_cls, **kwargs) -> FastAPI:
    app = FastAPI()
    app.add_middleware(middleware_cls, **kwargs)

    @app.get("/ping")
    async def ping() -> dict[str, str]:
        return {"ok": "yes"}

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/echo")
    async def echo(payload: dict) -> dict:
        return payload

    return app


async def _client(app: FastAPI):
    manager = LifespanManager(app)
    await manager.__aenter__()
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test"), manager


# --- Rate limiting ---------------------------------------------------------


async def test_rate_limit_blocks_after_limit() -> None:
    app = _app_with(RateLimitMiddleware, redis=FakeRedis(), limit=2, window_seconds=60)
    client, manager = await _client(app)
    try:
        assert (await client.get("/ping")).status_code == 200
        assert (await client.get("/ping")).status_code == 200
        assert (await client.get("/ping")).status_code == 429
    finally:
        await client.aclose()
        await manager.__aexit__(None, None, None)


async def test_rate_limit_exempts_health() -> None:
    app = _app_with(RateLimitMiddleware, redis=FakeRedis(), limit=1, window_seconds=60)
    client, manager = await _client(app)
    try:
        for _ in range(3):
            assert (await client.get("/health")).status_code == 200
    finally:
        await client.aclose()
        await manager.__aexit__(None, None, None)


async def test_rate_limit_disabled_is_noop() -> None:
    app = _app_with(RateLimitMiddleware, redis=FakeRedis(), enabled=False, limit=1)
    client, manager = await _client(app)
    try:
        for _ in range(3):
            assert (await client.get("/ping")).status_code == 200
    finally:
        await client.aclose()
        await manager.__aexit__(None, None, None)


async def test_rate_limit_fails_open_when_redis_down() -> None:
    app = _app_with(RateLimitMiddleware, redis=BrokenRedis(), limit=1, window_seconds=60)
    client, manager = await _client(app)
    try:
        for _ in range(3):
            assert (await client.get("/ping")).status_code == 200
    finally:
        await client.aclose()
        await manager.__aexit__(None, None, None)


# --- Body size -------------------------------------------------------------


@pytest.mark.parametrize(("body", "expected"), [({"a": "x"}, 200), ({"a": "x" * 500}, 413)])
async def test_body_size_cap(body: dict, expected: int) -> None:
    app = _app_with(MaxBodySizeMiddleware, max_bytes=64)
    client, manager = await _client(app)
    try:
        resp = await client.post("/echo", json=body)
        assert resp.status_code == expected
    finally:
        await client.aclose()
        await manager.__aexit__(None, None, None)


async def test_body_size_invalid_content_length_passes() -> None:
    app = _app_with(MaxBodySizeMiddleware, max_bytes=64)
    client, manager = await _client(app)
    try:
        resp = await client.post(
            "/echo",
            content=b"{}",
            headers={"content-length": "not-a-number", "content-type": "application/json"},
        )
        assert resp.status_code == 200
    finally:
        await client.aclose()
        await manager.__aexit__(None, None, None)
