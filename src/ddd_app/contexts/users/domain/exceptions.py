"""User-context exceptions, subclassing the shared kernel so the API maps them to HTTP once."""

from __future__ import annotations

from ddd_app.contexts.shared.domain.exceptions import ConflictError, EntityNotFoundError


class UserNotFoundError(EntityNotFoundError):
    def __init__(self, identifier: object) -> None:
        super().__init__("User", identifier)


class EmailAlreadyRegisteredError(ConflictError):
    def __init__(self, email: str) -> None:
        super().__init__(f"Email already registered: {email}")
