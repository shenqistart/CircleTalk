"""Alembic 迁移环境，支持多租户 schema。"""

import os
from logging.config import fileConfig

from alembic import context
from core.config.loader import ConfigLoader
from core.database.base import Base
from core.database.identifier import build_create_schema_sql, build_search_path_sql
from sqlalchemy import create_engine

# 导入所有模型，确保 Alembic 能检测到
import backend.domain.model.roundtable as roundtable_models  # noqa: F401
from backend.config.database_url import resolve_database_url
from backend.domain.model.user import User  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    app_config = ConfigLoader.load()
    tenant = os.environ.get("ALEMBIC_TENANT", "default")
    return resolve_database_url(app_config, async_driver=False, tenant=tenant)


def get_schema_name() -> str:
    app_config = ConfigLoader.load()
    tenant = os.environ.get("ALEMBIC_TENANT", "default")
    tenants = app_config.get("tenants", {})
    tenant_config = tenants.get(tenant, {})
    database_config = tenant_config.get("database", {})
    return database_config.get("name") or "public"


def quote_identifier(identifier: str) -> str:
    return f'"{identifier.replace(chr(34), chr(34) * 2)}"'


def run_migrations_offline() -> None:
    context.configure(url=get_url(), target_metadata=target_metadata, literal_binds=True)
    schema = get_schema_name()
    context.execute(f"CREATE SCHEMA IF NOT EXISTS {quote_identifier(schema)}")
    context.execute(f"SET search_path TO {quote_identifier(schema)}")
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(get_url())
    schema = get_schema_name()
    with connectable.connect() as connection:
        connection.execute(build_create_schema_sql(schema))
        connection.execute(build_search_path_sql(schema))
        connection.commit()

        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
