"""Reject over-large request bodies with HTTP 413.

Checks the ``Content-Length`` header up front so a huge upload is refused before it is read into
memory. Requests without a declared length pass through (there is nothing to enforce against).
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, max_bytes: int) -> None:
        super().__init__(app)
        self._max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                declared = int(content_length)
            except ValueError:
                declared = 0
            if declared > self._max_bytes:
                return JSONResponse(
                    status_code=413,
                    content={
                        "error": "RequestEntityTooLarge",
                        "detail": f"Request body exceeds {self._max_bytes} bytes",
                    },
                )
        return await call_next(request)
