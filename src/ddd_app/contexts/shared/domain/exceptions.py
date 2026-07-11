"""Framework-free domain exception hierarchy shared by every context.

The presentation layer maps these families to HTTP status codes in one place
(`presentation/api/errors.py`), so domain and application code never import a web framework.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base class for all domain/application errors."""


class DomainValidationError(DomainError):
    """A business rule / invariant was violated (maps to HTTP 422)."""


class EntityNotFoundError(DomainError):
    """A requested entity does not exist (maps to HTTP 404)."""

    def __init__(self, entity: str, identifier: object) -> None:
        super().__init__(f"{entity} not found: {identifier}")
        self.entity = entity
        self.identifier = identifier


class ConflictError(DomainError):
    """A uniqueness / state conflict (maps to HTTP 409)."""


class PermissionDeniedError(DomainError):
    """The caller is not allowed to perform the action (maps to HTTP 403)."""


class AuthenticationError(DomainError):
    """Authentication failed or credentials are missing (maps to HTTP 401)."""
