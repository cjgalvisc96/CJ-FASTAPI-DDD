"""Per-request database session dependency (no Unit of Work).

Opens one AsyncSession for the request and publishes it on the scoped-session contextvar. Write
routes open an explicit transaction with `async with session.begin()`; read routes just query.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ddd_app.presentation.api.dependencies import get_container


async def get_session(container=Depends(get_container)) -> AsyncIterator[AsyncSession]:
    database = container.shared.database()
    async with database.session_scope() as session:
        yield session
