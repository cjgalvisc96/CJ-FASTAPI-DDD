"""Generic HTTP pagination envelope that maps an application `Page[T]` to a response model."""

from __future__ import annotations

from collections.abc import Callable

from pydantic import BaseModel

from ddd_app.contexts.shared.application.page import Page


class PageResponse[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int

    @classmethod
    def from_page[S](cls, page: Page[S], mapper: Callable[[S], T]) -> PageResponse[T]:
        return cls(
            items=[mapper(item) for item in page.items],
            total=page.total,
            limit=page.limit,
            offset=page.offset,
        )
