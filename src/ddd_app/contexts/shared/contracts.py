"""Cross-context contracts — the ONLY channel bounded contexts use to talk to each other.

A bounded context NEVER imports another context's modules. Instead:

* the **shared** kernel declares a narrow contract (an ABC) plus its own small DTOs here;
* the **provider** context's data is exposed through an adapter that implements the contract, wired
  in ``core/di/adapters.py`` — the one place allowed to import a context's internals;
* the **consumer** context depends only on ``ddd_app.contexts.shared.contracts``.

This keeps contexts independent and the dependency direction explicit (a context depends on the
shared kernel, never on a sibling). ``users`` is currently the only business context, so it
*publishes* the ``UserDirectory`` contract here for future consumers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class UserRef:
    """A minimal, cross-context-safe view of a user (no domain internals leak across contexts)."""

    id: UUID
    email: str
    is_active: bool


class UserDirectory(ABC):
    """Contract published by ``users``: look up basic user facts from another context."""

    @abstractmethod
    async def find(self, user_id: UUID) -> UserRef | None: ...

    @abstractmethod
    async def exists(self, user_id: UUID) -> bool: ...
