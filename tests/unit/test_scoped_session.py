from __future__ import annotations

import pytest

from ddd_app.contexts.shared.infrastructure.db.scoped_session import current_session


def test_current_session_without_active_scope_raises() -> None:
    with pytest.raises(RuntimeError):
        current_session()
