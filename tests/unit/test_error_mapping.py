"""The domain-exception → HTTP mapping, including the generic fallback for a bare DomainError."""

from __future__ import annotations

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from ddd_app.contexts.shared.domain.exceptions import (
    ConflictError,
    DomainError,
    DomainValidationError,
    EntityNotFoundError,
    PermissionDeniedError,
)
from ddd_app.presentation.api.errors import register_exception_handlers


def _app_raising(exc: Exception) -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/boom")
    async def boom() -> None:
        raise exc

    return app


@pytest.mark.parametrize(
    ("exc", "expected"),
    [
        (EntityNotFoundError("User", "x"), 404),
        (ConflictError("dup"), 409),
        (DomainValidationError("bad"), 422),
        (PermissionDeniedError("nope"), 403),
        (DomainError("generic"), 400),  # fallback
    ],
)
async def test_exception_maps_to_status(exc: Exception, expected: int) -> None:
    app = _app_raising(exc)
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/boom")
    assert resp.status_code == expected
    assert resp.json()["error"] == type(exc).__name__
