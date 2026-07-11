"""The cross-context contract (shared.contracts.UserDirectory) works end-to-end when wired."""

from __future__ import annotations

import uuid

from ddd_app.contexts.users.domain.entities.user import User


async def test_user_directory_contract(container, session) -> None:
    repo = container.users.user_repository()
    user = User.register(email="a@b.com", full_name="Ann")
    await repo.add(user)

    directory = container.user_directory()

    assert await directory.exists(user.id) is True
    ref = await directory.find(user.id)
    assert ref is not None
    assert ref.email == "a@b.com"
    assert ref.is_active is True

    assert await directory.exists(uuid.uuid4()) is False
    assert await directory.find(uuid.uuid4()) is None
