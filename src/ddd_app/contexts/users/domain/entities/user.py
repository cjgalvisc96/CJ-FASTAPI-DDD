"""The User entity — a plain dataclass with behavior, no value objects, no aggregate root."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field

from ddd_app.contexts.shared.domain.exceptions import DomainValidationError

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Roles recognized for RBAC. Kept as a small module-level set (no enum) to stay simple.
VALID_ROLES = frozenset({"admin", "member"})
DEFAULT_ROLE = "member"


@dataclass(eq=False)
class User:
    """A user account. Fields are plain primitives; invariants live in `__post_init__`."""

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    email: str = ""
    full_name: str = ""
    role: str = DEFAULT_ROLE
    is_active: bool = True

    def __post_init__(self) -> None:
        self.email = self.email.strip().lower()
        self.full_name = self.full_name.strip()
        if not _EMAIL_RE.match(self.email):
            raise DomainValidationError(f"Invalid email: {self.email!r}")
        if not self.full_name:
            raise DomainValidationError("User full_name must not be empty")
        self.role = self._normalize_role(self.role)

    @staticmethod
    def _normalize_role(role: str) -> str:
        role = role.strip().lower()
        if role not in VALID_ROLES:
            raise DomainValidationError(
                f"Unknown role: {role!r} (expected one of {sorted(VALID_ROLES)})"
            )
        return role

    @classmethod
    def register(
        cls,
        *,
        email: str,
        full_name: str,
        role: str = DEFAULT_ROLE,
        user_id: uuid.UUID | None = None,
    ) -> User:
        """Factory for a brand-new user."""
        return cls(
            id=user_id or uuid.uuid4(),
            email=email,
            full_name=full_name,
            role=role,
        )

    def rename(self, full_name: str) -> None:
        full_name = full_name.strip()
        if not full_name:
            raise DomainValidationError("User full_name must not be empty")
        self.full_name = full_name

    def change_role(self, role: str) -> None:
        self.role = self._normalize_role(role)

    def deactivate(self) -> None:
        self.is_active = False

    def activate(self) -> None:
        self.is_active = True
