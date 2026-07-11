"""User HTTP routes. Zero business logic: auth → use case → serializer.

Writes run inside an explicit transaction (`async with session.begin()`); reads don't. `GET /{id}`
is served through the Redis read-through cache and role changes invalidate it.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ddd_app.contexts.shared.application.request_context import RequestContext
from ddd_app.presentation.api.caching import cached
from ddd_app.presentation.api.dependencies import (
    get_container,
    get_request_context,
    require_role,
)
from ddd_app.presentation.api.pagination import PageResponse
from ddd_app.presentation.api.runtime import get_session
from ddd_app.presentation.api.v1.users.serializers import (
    ChangeRoleRequest,
    RegisterUserRequest,
    UserResponse,
)

router = APIRouter(prefix="/users", tags=["users"])

_CACHE_NS = "users"


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    payload: RegisterUserRequest,
    _ctx: RequestContext = Depends(require_role("admin")),
    container=Depends(get_container),
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    command = container.users.register_user_command()
    async with session.begin():
        result = await command.execute(payload.to_input())
    return UserResponse.from_output(result)


@router.get("", response_model=PageResponse[UserResponse])
async def list_users(
    limit: int = 50,
    offset: int = 0,
    _ctx: RequestContext = Depends(get_request_context),
    container=Depends(get_container),
    session: AsyncSession = Depends(get_session),
) -> PageResponse[UserResponse]:
    query = container.users.list_users_query()
    page = await query.execute(limit=limit, offset=offset)
    return PageResponse.from_page(page, UserResponse.from_output)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    _ctx: RequestContext = Depends(get_request_context),
    container=Depends(get_container),
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    async def produce() -> UserResponse:
        query = container.users.get_user_query()
        return UserResponse.from_output(await query.execute(user_id))

    cache = container.shared.cache()
    return await cached(cache, _CACHE_NS, str(user_id), UserResponse, produce)


@router.patch("/{user_id}/role", response_model=UserResponse)
async def change_role(
    user_id: UUID,
    payload: ChangeRoleRequest,
    _ctx: RequestContext = Depends(require_role("admin")),
    container=Depends(get_container),
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    command = container.users.change_user_role_command()
    async with session.begin():
        result = await command.execute(user_id, payload.role)
    await container.shared.cache().invalidate(_CACHE_NS, str(user_id))
    return UserResponse.from_output(result)
