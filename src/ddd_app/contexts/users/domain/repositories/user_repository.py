"""Outbound (driven) port for user persistence — an ABC owned by the domain."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from ddd_app.contexts.users.domain.entities.user import User


class UserRepository(ABC):
    """Async repository returning domain entities. The concrete adapter lives in infrastructure."""

    @abstractmethod
    async def add(self, user: User) -> None: ...

    @abstractmethod
    async def get(self, user_id: uuid.UUID) -> User | None: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def list(self, *, limit: int = 50, offset: int = 0) -> list[User]: ...

    @abstractmethod
    async def count(self) -> int: ...

    @abstractmethod
    async def update(self, user: User) -> None: ...
