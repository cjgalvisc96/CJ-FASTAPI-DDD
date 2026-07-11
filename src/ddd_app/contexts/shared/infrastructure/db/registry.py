"""Single import point that registers every ORM model on `Base.metadata`.

Importing this module ensures `Base.metadata.create_all()` (used by the test suite) sees all tables.
Production/dev schema is owned by Atlas migrations, not `create_all`.
"""

from __future__ import annotations

from ddd_app.contexts.shared.infrastructure.db.base_model import Base
from ddd_app.contexts.users.infrastructure.db.models.user_model import UserModel

__all__ = ["Base", "UserModel"]
