from __future__ import annotations

import uuid

import pytest

from ddd_app.contexts.users.application.commands.change_user_role import ChangeUserRoleCommand
from ddd_app.contexts.users.application.commands.register_user import RegisterUserCommand
from ddd_app.contexts.users.application.dto.user_dto import RegisterUserInput
from ddd_app.contexts.users.domain.exceptions import (
    EmailAlreadyRegisteredError,
    UserNotFoundError,
)
from ddd_app.contexts.users.domain.services.email_uniqueness import EmailUniquenessChecker
from tests.unit.fakes import FakeUserRepository


async def test_register_user_persists_and_returns_output() -> None:
    repo = FakeUserRepository()
    command = RegisterUserCommand(repo, EmailUniquenessChecker(repo))
    out = await command.execute(RegisterUserInput(email="a@b.com", full_name="Ann", role="admin"))
    assert out.email == "a@b.com"
    assert out.role == "admin"
    assert await repo.count() == 1


async def test_register_user_rejects_duplicate_email() -> None:
    repo = FakeUserRepository()
    command = RegisterUserCommand(repo, EmailUniquenessChecker(repo))
    await command.execute(RegisterUserInput(email="a@b.com", full_name="Ann"))
    with pytest.raises(EmailAlreadyRegisteredError):
        await command.execute(RegisterUserInput(email="A@B.com", full_name="Other"))


async def test_change_role_updates_user() -> None:
    repo = FakeUserRepository()
    register = RegisterUserCommand(repo, EmailUniquenessChecker(repo))
    created = await register.execute(RegisterUserInput(email="a@b.com", full_name="Ann"))
    change = ChangeUserRoleCommand(repo)
    out = await change.execute(created.id, "admin")
    assert out.role == "admin"


async def test_change_role_missing_user_raises() -> None:
    repo = FakeUserRepository()
    change = ChangeUserRoleCommand(repo)
    with pytest.raises(UserNotFoundError):
        await change.execute(uuid.uuid4(), "admin")
