"""Generic pagination wrapper used by query use cases."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Page[T]:
    """A single page of results plus the total count for the whole set."""

    items: list[T]
    total: int
    limit: int
    offset: int
