"""The authenticated caller for the current request, carried via a contextvar.

Set once at the transport boundary (`get_request_context`) and readable anywhere downstream
without threading it through every call.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RequestContext:
    """Identity + roles of the caller (single-tenant: no tenant_id)."""

    user_id: UUID | None
    email: str | None = None
    roles: frozenset[str] = field(default_factory=frozenset)

    def has_role(self, role: str) -> bool:
        return role in self.roles


_current: ContextVar[RequestContext | None] = ContextVar("request_context", default=None)


@contextmanager
def bind_context(ctx: RequestContext) -> Generator[RequestContext]:
    token = _current.set(ctx)
    try:
        yield ctx
    finally:
        _current.reset(token)


def current_context() -> RequestContext | None:
    return _current.get()
