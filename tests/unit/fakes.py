"""In-memory test doubles for unit tests (no DB)."""

from __future__ import annotations

import uuid

from ddd_app.contexts.users.domain.entities.user import User
from ddd_app.contexts.users.domain.repositories.user_repository import UserRepository


class FakeUserRepository(UserRepository):
    def __init__(self) -> None:
        self._users: dict[uuid.UUID, User] = {}

    async def add(self, user: User) -> None:
        self._users[user.id] = user

    async def get(self, user_id: uuid.UUID) -> User | None:
        return self._users.get(user_id)

    async def get_by_email(self, email: str) -> User | None:
        email = email.strip().lower()
        return next((u for u in self._users.values() if u.email == email), None)

    async def list(self, *, limit: int = 50, offset: int = 0) -> list[User]:
        return list(self._users.values())[offset : offset + limit]

    async def count(self) -> int:
        return len(self._users)

    async def update(self, user: User) -> None:
        self._users[user.id] = user
