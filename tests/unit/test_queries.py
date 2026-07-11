from __future__ import annotations

import uuid

import pytest

from ddd_app.contexts.users.application.commands.register_user import RegisterUserCommand
from ddd_app.contexts.users.application.dto.user_dto import RegisterUserInput
from ddd_app.contexts.users.application.queries.get_user import GetUserByIdQuery
from ddd_app.contexts.users.application.queries.list_users import ListUsersQuery
from ddd_app.contexts.users.domain.exceptions import UserNotFoundError
from ddd_app.contexts.users.domain.services.email_uniqueness import EmailUniquenessChecker
from tests.unit.fakes import FakeUserRepository


async def test_get_user_returns_output() -> None:
    repo = FakeUserRepository()
    register = RegisterUserCommand(repo, EmailUniquenessChecker(repo))
    created = await register.execute(RegisterUserInput(email="a@b.com", full_name="Ann"))
    out = await GetUserByIdQuery(repo).execute(created.id)
    assert out.email == "a@b.com"


async def test_get_user_missing_raises() -> None:
    with pytest.raises(UserNotFoundError):
        await GetUserByIdQuery(FakeUserRepository()).execute(uuid.uuid4())


async def test_list_users_returns_page() -> None:
    repo = FakeUserRepository()
    register = RegisterUserCommand(repo, EmailUniquenessChecker(repo))
    await register.execute(RegisterUserInput(email="a@b.com", full_name="Ann"))
    await register.execute(RegisterUserInput(email="c@d.com", full_name="Cy"))
    page = await ListUsersQuery(repo).execute(limit=1, offset=0)
    assert page.total == 2
    assert len(page.items) == 1
    assert page.limit == 1
