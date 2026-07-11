"""Transport-boundary dependencies: container/settings access, Keycloak auth, RBAC."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from uuid import uuid4

from fastapi import Depends, Header, HTTPException, Request, status

from ddd_app.contexts.shared.application.request_context import RequestContext, bind_context
from ddd_app.contexts.shared.domain.exceptions import AuthenticationError
from ddd_app.core.config import Settings


def get_container(request: Request):
    return request.app.state.container


def get_settings_dep(request: Request) -> Settings:
    return request.app.state.settings


def _bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token.strip()


async def get_request_context(
    authorization: str | None = Header(default=None),
    x_dev_roles: str | None = Header(default=None),
    container=Depends(get_container),
    settings: Settings = Depends(get_settings_dep),
) -> AsyncIterator[RequestContext]:
    """Resolve the caller from a Keycloak Bearer token, binding it to the request contextvar.

    Dev backdoor: when DEBUG is on and no token is present, an `X-Dev-Roles` header fabricates a
    context so the API can be exercised locally without Keycloak.
    """
    ctx: RequestContext | None = None
    token = _bearer_token(authorization)
    if token:
        authenticator = container.users.keycloak_authenticator()
        try:
            claims = await authenticator.verify(token)
        except AuthenticationError as exc:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
        ctx = RequestContext(user_id=claims.subject, email=claims.email, roles=claims.roles)
    elif settings.debug and x_dev_roles is not None:
        roles = frozenset(r.strip().lower() for r in x_dev_roles.split(",") if r.strip())
        ctx = RequestContext(
            user_id=uuid4(), email="dev@example.com", roles=roles or frozenset({"member"})
        )

    if ctx is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid credentials")

    with bind_context(ctx):
        yield ctx


def require_role(role: str) -> Callable[..., RequestContext]:
    """RBAC dependency factory: 403 unless the caller has `role`."""

    def _checker(ctx: RequestContext = Depends(get_request_context)) -> RequestContext:
        if not ctx.has_role(role):
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail=f"Requires role: {role}")
        return ctx

    return _checker
