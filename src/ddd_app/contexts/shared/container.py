"""DI wiring for cross-cutting shared infrastructure (DB engine, Redis, cache)."""

from __future__ import annotations

from dependency_injector import containers, providers
from redis.asyncio import Redis

from ddd_app.contexts.shared.infrastructure.cache.redis_cache import RedisCache
from ddd_app.contexts.shared.infrastructure.db.session import Database


class SharedContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    database = providers.Singleton(
        Database,
        dsn=config.database_dsn,
        echo=config.db_echo,
        pool_size=config.db_pool_size,
        max_overflow=config.db_pool_max_overflow,
    )

    redis = providers.Singleton(Redis.from_url, config.redis_dsn)

    cache = providers.Singleton(
        RedisCache,
        redis=redis,
        enabled=config.cache_enable,
        namespaces=config.cache_namespace_list,
    )
