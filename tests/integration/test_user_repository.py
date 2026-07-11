"""Integration test: SqlAlchemyUserRepository against a real (SQLite) session."""

from __future__ import annotations

import uuid

import pytest

from ddd_app.contexts.users.domain.entities.user import User
from ddd_app.contexts.users.infrastructure.db.repositories.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)


async def test_add_get_and_get_by_email(session) -> None:
    repo = SqlAlchemyUserRepository()
    user = User.register(email="a@b.com", full_name="Ann", role="admin")
    await repo.add(user)

    fetched = await repo.get(user.id)
    assert fetched is not None
    assert fetched.email == "a@b.com"
    assert fetched.role == "admin"

    by_email = await repo.get_by_email("A@B.com")
    assert by_email is not None
    assert by_email.id == user.id


async def test_get_missing_returns_none(session) -> None:
    repo = SqlAlchemyUserRepository()
    assert await repo.get(uuid.uuid4()) is None


async def test_list_and_count(session) -> None:
    repo = SqlAlchemyUserRepository()
    await repo.add(User.register(email="a@b.com", full_name="A"))
    await repo.add(User.register(email="c@d.com", full_name="C"))

    assert await repo.count() == 2
    page = await repo.list(limit=1, offset=0)
    assert len(page) == 1


async def test_update_persists_changes(session) -> None:
    repo = SqlAlchemyUserRepository()
    user = User.register(email="a@b.com", full_name="A")
    await repo.add(user)

    user.change_role("admin")
    await repo.update(user)

    reloaded = await repo.get(user.id)
    assert reloaded is not None
    assert reloaded.role == "admin"


async def test_update_missing_raises(session) -> None:
    repo = SqlAlchemyUserRepository()
    with pytest.raises(ValueError):
        await repo.update(User.register(email="a@b.com", full_name="A"))
