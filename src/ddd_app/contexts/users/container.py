"""DI wiring for the users context: repository, domain service, use cases, Keycloak auth."""

from __future__ import annotations

from dependency_injector import containers, providers

from ddd_app.contexts.users.application.commands.change_user_role import ChangeUserRoleCommand
from ddd_app.contexts.users.application.commands.register_user import RegisterUserCommand
from ddd_app.contexts.users.application.queries.get_user import GetUserByIdQuery
from ddd_app.contexts.users.application.queries.list_users import ListUsersQuery
from ddd_app.contexts.users.domain.services.email_uniqueness import EmailUniquenessChecker
from ddd_app.contexts.users.infrastructure.auth.oidc import OidcAuthenticator
from ddd_app.contexts.users.infrastructure.db.repositories.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)


class UsersContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    # Fresh per resolution; resolves the request session from the contextvar.
    user_repository = providers.Factory(SqlAlchemyUserRepository)

    email_uniqueness = providers.Factory(EmailUniquenessChecker, repository=user_repository)

    register_user_command = providers.Factory(
        RegisterUserCommand,
        repository=user_repository,
        uniqueness=email_uniqueness,
    )
    change_user_role_command = providers.Factory(ChangeUserRoleCommand, repository=user_repository)
    get_user_query = providers.Factory(GetUserByIdQuery, repository=user_repository)
    list_users_query = providers.Factory(ListUsersQuery, repository=user_repository)

    # Effective OIDC endpoints: explicit OIDC_* overrides (e.g. Cognito) or Keycloak-derived.
    oidc_authenticator = providers.Singleton(
        OidcAuthenticator,
        issuer=config.oidc_issuer_effective,
        jwks_url=config.oidc_jwks_url_effective,
        client_id=config.oidc_client_id_effective,
        verify_audience=config.keycloak_verify_audience,
    )
