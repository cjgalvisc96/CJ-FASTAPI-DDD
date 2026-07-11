"""Domain service: enforce the cross-set invariant that emails are unique."""

from __future__ import annotations

from ddd_app.contexts.users.domain.exceptions import EmailAlreadyRegisteredError
from ddd_app.contexts.users.domain.repositories.user_repository import UserRepository


class EmailUniquenessChecker:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def ensure_unique(self, email: str) -> None:
        if await self._repository.get_by_email(email) is not None:
            raise EmailAlreadyRegisteredError(email)
