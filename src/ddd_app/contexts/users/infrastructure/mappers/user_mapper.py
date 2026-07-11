"""The only place that knows both the User entity and the UserModel shapes."""

from __future__ import annotations

from ddd_app.contexts.users.domain.entities.user import User
from ddd_app.contexts.users.infrastructure.db.models.user_model import UserModel


class UserMapper:
    @staticmethod
    def to_entity(model: UserModel) -> User:
        return User(
            id=model.id,
            email=model.email,
            full_name=model.full_name,
            role=model.role,
            is_active=model.is_active,
        )

    @staticmethod
    def to_model(entity: User) -> UserModel:
        return UserModel(
            id=entity.id,
            email=entity.email,
            full_name=entity.full_name,
            role=entity.role,
            is_active=entity.is_active,
        )

    @staticmethod
    def apply(entity: User, model: UserModel) -> None:
        """Copy entity state onto an already-managed model (for updates)."""
        model.email = entity.email
        model.full_name = entity.full_name
        model.role = entity.role
        model.is_active = entity.is_active
