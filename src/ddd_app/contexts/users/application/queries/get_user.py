"""Read use case: fetch a single user by id."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from ddd_app.contexts.users.application.dto.user_dto import UserOutput
from ddd_app.contexts.users.domain.exceptions import UserNotFoundError

if TYPE_CHECKING:
    from ddd_app.contexts.users.domain.repositories.user_repository import UserRepository


class GetUserByIdQuery:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def execute(self, user_id: uuid.UUID) -> UserOutput:
        user = await self._repository.get(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        return UserOutput.from_entity(user)
