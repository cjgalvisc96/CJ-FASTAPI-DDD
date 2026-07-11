from __future__ import annotations

import uuid

import pytest

from ddd_app.contexts.shared.domain.exceptions import DomainValidationError
from ddd_app.contexts.users.domain.entities.user import User


def test_register_normalizes_email_and_name() -> None:
    user = User.register(email="  ADA@Example.COM ", full_name="  Ada Lovelace  ")
    assert user.email == "ada@example.com"
    assert user.full_name == "Ada Lovelace"
    assert user.role == "member"
    assert user.is_active is True
    assert isinstance(user.id, uuid.UUID)


@pytest.mark.parametrize("email", ["not-an-email", "a@b", "@b.com", ""])
def test_invalid_email_rejected(email: str) -> None:
    with pytest.raises(DomainValidationError):
        User.register(email=email, full_name="X")


def test_empty_name_rejected() -> None:
    with pytest.raises(DomainValidationError):
        User.register(email="a@b.com", full_name="   ")


def test_unknown_role_rejected() -> None:
    with pytest.raises(DomainValidationError):
        User.register(email="a@b.com", full_name="X", role="superuser")


def test_change_role_and_deactivate() -> None:
    user = User.register(email="a@b.com", full_name="X")
    user.change_role("admin")
    assert user.role == "admin"
    user.deactivate()
    assert user.is_active is False
    user.activate()
    assert user.is_active is True


def test_change_role_validates() -> None:
    user = User.register(email="a@b.com", full_name="X")
    with pytest.raises(DomainValidationError):
        user.change_role("root")


def test_rename_updates_and_trims() -> None:
    user = User.register(email="a@b.com", full_name="Old")
    user.rename("  New Name  ")
    assert user.full_name == "New Name"


def test_rename_empty_rejected() -> None:
    user = User.register(email="a@b.com", full_name="Old")
    with pytest.raises(DomainValidationError):
        user.rename("   ")
