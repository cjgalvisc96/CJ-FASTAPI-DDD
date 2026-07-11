"""Declarative base + a shared ORM mixin with the columns every table carries."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import Uuid


class Base(DeclarativeBase):
    """Root declarative base; `Base.metadata` is the single schema registry."""


class BaseModel(Base):
    """Abstract mixin: UUID primary key, audit timestamps, soft-delete flag."""

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
