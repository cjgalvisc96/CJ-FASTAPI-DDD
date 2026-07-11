"""SQLAlchemy implementation of the UserRepository port.

Resolves the current request session from the scoped-session contextvar, so it needs no session
argument and stays a plain `Factory` in the DI container. Translation to/from the domain entity is
delegated to `UserMapper`.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select

from ddd_app.contexts.shared.infrastructure.db.scoped_session import current_session
from ddd_app.contexts.users.domain.entities.user import User
from ddd_app.contexts.users.domain.repositories.user_repository import UserRepository
from ddd_app.contexts.users.infrastructure.db.models.user_model import UserModel
from ddd_app.contexts.users.infrastructure.mappers.user_mapper import UserMapper


class SqlAlchemyUserRepository(UserRepository):
    async def add(self, user: User) -> None:
        session = current_session()
        session.add(UserMapper.to_model(user))
        await session.flush()

    async def get(self, user_id: uuid.UUID) -> User | None:
        model = await current_session().get(UserModel, user_id)
        return UserMapper.to_entity(model) if model is not None else None

    async def get_by_email(self, email: str) -> User | None:
        result = await current_session().execute(
            select(UserModel).where(UserModel.email == email.strip().lower())
        )
        model = result.scalar_one_or_none()
        return UserMapper.to_entity(model) if model is not None else None

    async def list(self, *, limit: int = 50, offset: int = 0) -> list[User]:
        result = await current_session().execute(
            select(UserModel).order_by(UserModel.created_at).limit(limit).offset(offset)
        )
        return [UserMapper.to_entity(m) for m in result.scalars().all()]

    async def count(self) -> int:
        result = await current_session().execute(select(func.count()).select_from(UserModel))
        return int(result.scalar_one())

    async def update(self, user: User) -> None:
        session = current_session()
        model = await session.get(UserModel, user.id)
        if model is None:
            raise ValueError(f"User not found for update: {user.id}")
        UserMapper.apply(user, model)
        await session.flush()
