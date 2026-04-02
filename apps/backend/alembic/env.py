"""Alembic 迁移环境，支持多租户 schema。"""

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

from core.config.loader import ConfigLoader
from core.database.base import Base

# 导入所有模型，确保 Alembic 能检测到
from backend.domain.user.model.user import User  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    app_config = ConfigLoader.load()
    db_config = app_config.get("database", {})
    tenants = app_config.get("tenants", {})
    tenant = os.environ.get("ALEMBIC_TENANT", "default")
    db_name = tenants.get(tenant, {}).get("database", {}).get("name", "bedrock")
    return (
        f"postgresql+psycopg://{db_config.get('username', 'postgres')}"
        f":{db_config.get('password', 'postgres')}"
        f"@{db_config.get('host', 'localhost')}"
        f":{db_config.get('port', 5432)}"
        f"/{db_name}"
    )


def run_migrations_offline() -> None:
    context.configure(url=get_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(get_url())
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
