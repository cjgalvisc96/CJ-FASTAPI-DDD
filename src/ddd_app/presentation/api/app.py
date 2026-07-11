"""FastAPI app assembly. The app receives its settings + DI container (injectable for tests)."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ddd_app.core.config import Settings, get_settings
from ddd_app.core.di.container import ApplicationContainer, build_container
from ddd_app.presentation.api.errors import register_exception_handlers
from ddd_app.presentation.api.middleware.body_size import MaxBodySizeMiddleware
from ddd_app.presentation.api.middleware.rate_limit import RateLimitMiddleware
from ddd_app.presentation.api.v1.users.routers import router as users_router


def create_app(
    *,
    settings: Settings | None = None,
    container: ApplicationContainer | None = None,
) -> FastAPI:
    app_settings = settings or get_settings()
    app_container = container or build_container(app_settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        app.state.container = app_container
        app.state.settings = app_settings
        yield
        with suppress(Exception):
            await app_container.shared.database().dispose()
        with suppress(Exception):
            await app_container.shared.cache().close()

    app = FastAPI(title="CJ FastAPI DDD", version="0.1.0", lifespan=lifespan)
    # Available before lifespan runs too (tests, sync access).
    app.state.container = app_container
    app.state.settings = app_settings

    # Middleware runs outermost-first (Starlette applies them in reverse order of addition), so the
    # effective order is: CORS → rate limit → body-size cap → routes.
    app.add_middleware(MaxBodySizeMiddleware, max_bytes=app_settings.max_request_body_bytes)
    app.add_middleware(
        RateLimitMiddleware,
        redis=app_container.shared.redis(),
        enabled=app_settings.rate_limit_enabled,
        limit=app_settings.rate_limit_requests,
        window_seconds=app_settings.rate_limit_window_seconds,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origin_list,
        allow_methods=app_settings.cors_method_list,
        allow_headers=app_settings.cors_header_list,
    )

    app.include_router(users_router, prefix="/api/v1")
    register_exception_handlers(app)

    @app.get("/health", tags=["meta"])
    async def health() -> JSONResponse:
        statuses: dict[str, str] = {}
        code = 200
        try:
            await app_container.shared.database().ping()
            statuses["database"] = "ok"
        except Exception as exc:
            statuses["database"] = f"error: {exc}"
            code = 503
        try:
            await app_container.shared.cache().ping()
            statuses["redis"] = "ok"
        except Exception as exc:
            statuses["redis"] = f"error: {exc}"
            code = 503
        return JSONResponse(status_code=code, content=statuses)

    return app
