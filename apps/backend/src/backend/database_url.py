"""Shared database URL resolution for runtime and Alembic."""

import os
from typing import Any


def normalize_postgres_url(url: str) -> str:
    value = url.strip()
    if not value:
        msg = "DATABASE_URL is empty"
        raise ValueError(msg)
    if value.startswith("postgres://"):
        value = "postgresql://" + value.removeprefix("postgres://")
    if value.startswith("postgresql://"):
        return "postgresql+psycopg://" + value.removeprefix("postgresql://")
    return value


def resolve_database_url(config: dict[str, Any], tenant: str = "default") -> str:
    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        return normalize_postgres_url(env_url)

    db_config = config.get("database", {})
    tenants = config.get("tenants", {})
    db_name = tenants.get(tenant, {}).get("database", {}).get("name", "bedrock")
    return normalize_postgres_url(
        "postgresql://"
        f"{db_config.get('username', 'postgres')}:{db_config.get('password', 'postgres')}"
        f"@{db_config.get('host', 'localhost')}:{db_config.get('port', 5432)}/{db_name}"
    )
