"""SQLAlchemy model for users. Carries only its own columns; the rest come from BaseModel."""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from ddd_app.contexts.shared.infrastructure.db.base_model import BaseModel


class UserModel(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="member")
