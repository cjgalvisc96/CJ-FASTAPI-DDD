"""Cross-context adapters — the ONE place allowed to import a context's internals.

Each adapter satisfies a contract declared in ``ddd_app.contexts.shared.contracts`` using a
*provider* context's repository, translating its entity into the contract's own DTO. Adapters are
wired into the root ``ApplicationContainer`` and injected into consumers, so no context imports a
sibling. See ``ddd_app.contexts.shared.contracts`` for the full convention.
"""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from ddd_app.contexts.shared.contracts import UserDirectory, UserRef
from ddd_app.contexts.users.domain.repositories.user_repository import UserRepository


class UsersUserDirectory(UserDirectory):
    """Satisfies the shared ``UserDirectory`` contract from the users repository.

    Takes a *factory* (not an instance) so each call resolves a fresh repository bound to the
    current request session.
    """

    def __init__(self, user_repository_factory: Callable[[], UserRepository]) -> None:
        self._factory = user_repository_factory

    async def find(self, user_id: UUID) -> UserRef | None:
        user = await self._factory().get(user_id)
        if user is None:
            return None
        return UserRef(id=user.id, email=user.email, is_active=user.is_active)

    async def exists(self, user_id: UUID) -> bool:
        return await self.find(user_id) is not None
