"""Map framework-free domain exceptions to HTTP responses in one place."""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from ddd_app.contexts.shared.domain.exceptions import (
    AuthenticationError,
    ConflictError,
    DomainError,
    DomainValidationError,
    EntityNotFoundError,
    PermissionDeniedError,
)

_STATUS_MAP: dict[type[Exception], int] = {
    EntityNotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    DomainValidationError: 422,  # Unprocessable Content
    PermissionDeniedError: status.HTTP_403_FORBIDDEN,
    AuthenticationError: status.HTTP_401_UNAUTHORIZED,
}


def register_exception_handlers(app: FastAPI) -> None:
    async def _handle(request: Request, exc: Exception) -> JSONResponse:
        code = next(
            (c for t, c in _STATUS_MAP.items() if isinstance(exc, t)),
            status.HTTP_400_BAD_REQUEST,
        )
        return JSONResponse(
            status_code=code,
            content={"error": type(exc).__name__, "detail": str(exc)},
        )

    # Register the specific families plus the base DomainError, which falls back to 400 for any
    # domain error not explicitly mapped. Starlette resolves the most specific handler by MRO.
    for exc_type in (*_STATUS_MAP, DomainError):
        app.add_exception_handler(exc_type, _handle)
