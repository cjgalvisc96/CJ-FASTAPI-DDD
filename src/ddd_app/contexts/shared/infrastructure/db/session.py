"""Async SQLAlchemy engine + session factory.

`session_scope()` opens one AsyncSession, binds it to the scoped-session contextvar for the
duration of the request, and closes it on exit. It does NOT commit — write routes open an explicit
transaction via `async with session.begin()`; reads simply query. There is no Unit of Work.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ddd_app.contexts.shared.infrastructure.db.scoped_session import (
    reset_current_session,
    set_current_session,
)


class Database:
    """Owns the async engine and hands out sessions."""

    def __init__(
        self,
        dsn: str,
        *,
        echo: bool = False,
        pool_size: int = 10,
        max_overflow: int = 20,
    ) -> None:
        # SQLite (tests) does not accept the QueuePool sizing / pre-ping args.
        is_sqlite = dsn.startswith("sqlite")
        kwargs: dict[str, object] = {"echo": echo}
        if not is_sqlite:
            kwargs.update(
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_pre_ping=True,
            )
        self._engine: AsyncEngine = create_async_engine(dsn, **kwargs)
        self._sessionmaker = async_sessionmaker(
            self._engine, expire_on_commit=False, class_=AsyncSession
        )

    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    @asynccontextmanager
    async def session_scope(self) -> AsyncGenerator[AsyncSession]:
        """Open a request-scoped session and publish it on the contextvar."""
        session = self._sessionmaker()
        token = set_current_session(session)
        try:
            yield session
        finally:
            reset_current_session(token)
            await session.close()

    async def ping(self) -> None:
        from sqlalchemy import text

        async with self._engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

    async def dispose(self) -> None:
        await self._engine.dispose()
