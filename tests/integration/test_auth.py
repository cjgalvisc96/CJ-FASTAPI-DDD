"""Auth paths: Keycloak Bearer token (via an overridden authenticator), malformed header, health."""

from __future__ import annotations

import uuid

import pytest
from asgi_lifespan import LifespanManager
from dependency_injector import providers
from httpx import ASGITransport, AsyncClient

from ddd_app.contexts.shared.domain.exceptions import AuthenticationError
from ddd_app.contexts.users.infrastructure.auth.oidc import OidcClaims
from ddd_app.core.config import Settings
from ddd_app.presentation.api.app import create_app


class FakeAuthenticator:
    def __init__(self, claims: OidcClaims | None = None, error: Exception | None = None) -> None:
        self._claims = claims
        self._error = error

    async def verify(self, token: str) -> OidcClaims:
        if self._error is not None:
            raise self._error
        assert self._claims is not None
        return self._claims


async def _client(container):
    settings = Settings(_env_file=None)
    app = create_app(settings=settings, container=container)
    manager = LifespanManager(app)
    await manager.__aenter__()
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test"), manager


async def test_valid_bearer_token_authenticates(container) -> None:
    claims = OidcClaims(subject=uuid.uuid4(), email="a@b.com", roles=frozenset({"admin"}))
    container.users.oidc_authenticator.override(providers.Object(FakeAuthenticator(claims)))
    client, manager = await _client(container)
    try:
        resp = await client.get("/api/v1/users", headers={"Authorization": "Bearer good-token"})
        assert resp.status_code == 200
    finally:
        await client.aclose()
        await manager.__aexit__(None, None, None)


async def test_invalid_bearer_token_is_401(container) -> None:
    container.users.oidc_authenticator.override(
        providers.Object(FakeAuthenticator(error=AuthenticationError("bad")))
    )
    client, manager = await _client(container)
    try:
        resp = await client.get("/api/v1/users", headers={"Authorization": "Bearer bad-token"})
        assert resp.status_code == 401
    finally:
        await client.aclose()
        await manager.__aexit__(None, None, None)


@pytest.mark.parametrize("header", ["Token abc", "Bearer", "Basic zzz"])
async def test_malformed_authorization_header_is_401(container, header: str) -> None:
    client, manager = await _client(container)
    try:
        resp = await client.get("/api/v1/users", headers={"Authorization": header})
        assert resp.status_code == 401
    finally:
        await client.aclose()
        await manager.__aexit__(None, None, None)


async def test_health_reports_database_ok(container) -> None:
    client, manager = await _client(container)
    try:
        resp = await client.get("/health")
        body = resp.json()
        assert body["database"] == "ok"
        assert "redis" in body
    finally:
        await client.aclose()
        await manager.__aexit__(None, None, None)
