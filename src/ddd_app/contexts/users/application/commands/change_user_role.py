"""Write use case: change a user's role."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from ddd_app.contexts.users.application.dto.user_dto import UserOutput
from ddd_app.contexts.users.domain.exceptions import UserNotFoundError

if TYPE_CHECKING:
    from ddd_app.contexts.users.domain.repositories.user_repository import UserRepository


class ChangeUserRoleCommand:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def execute(self, user_id: uuid.UUID, role: str) -> UserOutput:
        user = await self._repository.get(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        user.change_role(role)
        await self._repository.update(user)
        return UserOutput.from_entity(user)
