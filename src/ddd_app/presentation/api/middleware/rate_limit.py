"""Redis fixed-window rate-limit middleware.

Counts requests per client IP in a fixed time window using a Redis ``INCR`` + ``EXPIRE``. Meta
endpoints (health, docs) are exempt, and the limiter **fails open** — if Redis is unreachable the
request proceeds rather than erroring, so a cache outage never takes the API down.
"""

from __future__ import annotations

from collections.abc import Iterable

from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

_EXEMPT_PATHS = frozenset({"/", "/health", "/docs", "/redoc", "/openapi.json"})


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        redis: Redis,
        enabled: bool = True,
        limit: int = 100,
        window_seconds: int = 60,
        exempt_paths: Iterable[str] = _EXEMPT_PATHS,
    ) -> None:
        super().__init__(app)
        self._redis = redis
        self._enabled = enabled
        self._limit = limit
        self._window = window_seconds
        self._exempt = frozenset(exempt_paths)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not self._enabled or request.url.path in self._exempt:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"ratelimit:{client_ip}"
        try:
            count = await self._redis.incr(key)
            if count == 1:
                await self._redis.expire(key, self._window)
        except Exception:
            return await call_next(request)

        if count > self._limit:
            return JSONResponse(
                status_code=429,
                content={"error": "RateLimitExceeded", "detail": "Too many requests"},
            )
        return await call_next(request)
