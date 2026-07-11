"""Per-request AsyncSession carried via a contextvar.

Repositories resolve the current session through `current_session()` instead of receiving it as an
argument, so they can stay simple `Factory` providers in the DI container. The session is set by the
`get_session` request dependency (there is no Unit of Work abstraction).
"""

from __future__ import annotations

from contextvars import ContextVar, Token

from sqlalchemy.ext.asyncio import AsyncSession

_current_session: ContextVar[AsyncSession | None] = ContextVar("current_session", default=None)


def set_current_session(session: AsyncSession) -> Token[AsyncSession | None]:
    return _current_session.set(session)


def reset_current_session(token: Token[AsyncSession | None]) -> None:
    _current_session.reset(token)


def current_session() -> AsyncSession:
    session = _current_session.get()
    if session is None:
        raise RuntimeError("No active database session for this request")
    return session
