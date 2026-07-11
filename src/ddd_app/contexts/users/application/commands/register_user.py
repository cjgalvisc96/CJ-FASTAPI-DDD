"""Write use case: register a new user."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ddd_app.contexts.users.application.dto.user_dto import RegisterUserInput, UserOutput
from ddd_app.contexts.users.domain.entities.user import User

if TYPE_CHECKING:
    from ddd_app.contexts.users.domain.repositories.user_repository import UserRepository
    from ddd_app.contexts.users.domain.services.email_uniqueness import EmailUniquenessChecker


class RegisterUserCommand:
    def __init__(self, repository: UserRepository, uniqueness: EmailUniquenessChecker) -> None:
        self._repository = repository
        self._uniqueness = uniqueness

    async def execute(self, data: RegisterUserInput) -> UserOutput:
        user = User.register(email=data.email, full_name=data.full_name, role=data.role)
        await self._uniqueness.ensure_unique(user.email)
        await self._repository.add(user)
        return UserOutput.from_entity(user)
