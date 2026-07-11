from __future__ import annotations

from ddd_app.contexts.users.application.commands.register_user import RegisterUserCommand
from ddd_app.core.config import Settings
from ddd_app.core.di.container import build_container
from ddd_app.core.logging import configure_logging, get_logger


def test_build_container_from_settings() -> None:
    container = build_container(Settings(_env_file=None))
    # Providers resolve without touching the network.
    assert isinstance(container.users.register_user_command(), RegisterUserCommand)
    assert container.user_directory() is not None
    assert container.config.database_dsn() is not None


def test_build_container_defaults_to_get_settings() -> None:
    container = build_container()
    assert container.users.list_users_query() is not None


def test_logging_configures_and_returns_logger() -> None:
    configure_logging("INFO")
    logger = get_logger("ddd_app.test")
    assert logger.name == "ddd_app.test"
