"""End-to-end API test over the SQLite container, using the DEBUG dev-role backdoor."""

from __future__ import annotations

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from ddd_app.core.config import Settings
from ddd_app.presentation.api.app import create_app

ADMIN = {"X-Dev-Roles": "admin"}
MEMBER = {"X-Dev-Roles": "member"}


@pytest.fixture
async def client(container):
    settings = Settings(_env_file=None)  # defaults → debug=True, backdoor enabled
    app = create_app(settings=settings, container=container)
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


async def test_register_get_list_and_change_role(client: AsyncClient) -> None:
    created = await client.post(
        "/api/v1/users",
        headers=ADMIN,
        json={"email": "ada@example.com", "full_name": "Ada Lovelace", "role": "member"},
    )
    assert created.status_code == 201, created.text
    user_id = created.json()["id"]

    got = await client.get(f"/api/v1/users/{user_id}", headers=MEMBER)
    assert got.status_code == 200
    assert got.json()["email"] == "ada@example.com"

    listed = await client.get("/api/v1/users", headers=MEMBER)
    assert listed.status_code == 200
    body = listed.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1

    changed = await client.patch(
        f"/api/v1/users/{user_id}/role", headers=ADMIN, json={"role": "admin"}
    )
    assert changed.status_code == 200
    assert changed.json()["role"] == "admin"


async def test_duplicate_email_conflicts(client: AsyncClient) -> None:
    payload = {"email": "dup@example.com", "full_name": "Dup"}
    first = await client.post("/api/v1/users", headers=ADMIN, json=payload)
    assert first.status_code == 201
    second = await client.post("/api/v1/users", headers=ADMIN, json=payload)
    assert second.status_code == 409


async def test_missing_credentials_is_401(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/users")
    assert resp.status_code == 401


@pytest.mark.parametrize("params", ["limit=0", "limit=201", "limit=999999", "offset=-1"])
async def test_pagination_bounds_rejected(client: AsyncClient, params: str) -> None:
    resp = await client.get(f"/api/v1/users?{params}", headers=MEMBER)
    assert resp.status_code == 422


async def test_non_admin_cannot_create_403(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/users",
        headers=MEMBER,
        json={"email": "x@example.com", "full_name": "X"},
    )
    assert resp.status_code == 403
