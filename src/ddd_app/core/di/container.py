"""Composition root: the root container nests one container per bounded context."""

from __future__ import annotations

from dependency_injector import containers, providers

from ddd_app.contexts.shared.container import SharedContainer
from ddd_app.contexts.users.container import UsersContainer
from ddd_app.core.config import Settings, get_settings
from ddd_app.core.di.adapters import UsersUserDirectory


class ApplicationContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    shared = providers.Container(SharedContainer, config=config)
    users = providers.Container(UsersContainer, config=config)

    # Cross-context contract implementations (shared.contracts), wired at the composition root.
    # A consumer context would receive this via `providers.Dependency()` in its own container.
    user_directory = providers.Factory(
        UsersUserDirectory,
        user_repository_factory=users.user_repository.provider,
    )


def build_container(settings: Settings | None = None) -> ApplicationContainer:
    settings = settings or get_settings()
    container = ApplicationContainer()
    container.config.from_dict(settings.as_provider_dict())
    return container
