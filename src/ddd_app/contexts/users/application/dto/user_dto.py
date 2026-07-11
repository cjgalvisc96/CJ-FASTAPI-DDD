"""Application-boundary DTOs. Input carries raw primitives; output flattens the entity."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from ddd_app.contexts.users.domain.entities.user import DEFAULT_ROLE, User


@dataclass(frozen=True, slots=True)
class RegisterUserInput:
    email: str
    full_name: str
    role: str = DEFAULT_ROLE


@dataclass(frozen=True, slots=True)
class UserOutput:
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool

    @classmethod
    def from_entity(cls, user: User) -> UserOutput:
        return cls(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
        )
