"""Idempotent demo-data seeder (`ddd-seed` console script).

Runs the real RegisterUser use case inside a transaction; skips users that already exist so it is
safe to run repeatedly. Assumes the schema is already migrated (Atlas).
"""

from __future__ import annotations

import asyncio

from ddd_app.contexts.users.application.dto.user_dto import RegisterUserInput
from ddd_app.contexts.users.domain.exceptions import EmailAlreadyRegisteredError
from ddd_app.core.config import get_settings
from ddd_app.core.di.container import build_container
from ddd_app.core.logging import configure_logging, get_logger

_DEMO_USERS = [
    RegisterUserInput(email="admin@example.com", full_name="Ada Admin", role="admin"),
    RegisterUserInput(email="member@example.com", full_name="Max Member", role="member"),
]


async def _seed() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    logger = get_logger("seed")
    container = build_container(settings)
    database = container.shared.database()
    try:
        async with database.session_scope() as session, session.begin():
            command = container.users.register_user_command()
            for demo in _DEMO_USERS:
                try:
                    await command.execute(demo)
                    logger.info("seeded user %s", demo.email)
                except EmailAlreadyRegisteredError:
                    logger.info("user %s already exists, skipping", demo.email)
    finally:
        await database.dispose()


def main() -> None:
    asyncio.run(_seed())
