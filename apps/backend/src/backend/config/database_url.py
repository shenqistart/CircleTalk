"""Shared database URL resolver for runtime and Alembic."""

from __future__ import annotations

import os
from urllib.parse import urlsplit, urlunsplit

from core.config.loader import ConfigLoader

_SYNC_DRIVER = "postgresql+psycopg"
_ASYNC_DRIVER = "postgresql+psycopg"


def normalize_database_url(url: str, *, async_driver: bool = True) -> str:
    """Normalize Render/Postgres URLs into SQLAlchemy psycopg URLs."""
    stripped = url.strip()
    if not stripped:
        msg = "DATABASE_URL is empty"
        raise ValueError(msg)
    parsed = urlsplit(stripped)
    if not parsed.scheme or not parsed.netloc:
        msg = "DATABASE_URL must include scheme and host"
        raise ValueError(msg)
    driver = _ASYNC_DRIVER if async_driver else _SYNC_DRIVER
    if parsed.scheme in {"postgres", "postgresql", "postgresql+psycopg2", "postgresql+psycopg"}:
        return urlunsplit((driver, parsed.netloc, parsed.path, parsed.query, parsed.fragment))
    return stripped


def resolve_database_url(config: dict | None = None, *, async_driver: bool = True, tenant: str | None = None) -> str:
    """Resolve DATABASE_URL first, then existing YAML config fallback."""
    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        return normalize_database_url(env_url, async_driver=async_driver)

    app_config = config or ConfigLoader.load()
    db_config = app_config.get("database", {})
    tenants = app_config.get("tenants", {})
    tenant_name = tenant or os.environ.get("ALEMBIC_TENANT", "default")
    tenant_config = tenants.get(tenant_name) or next(iter(tenants.values()), {})
    db_name = tenant_config.get("database", {}).get("name", "bedrock")
    raw = (
        f"postgresql://{db_config.get('username', 'postgres')}"
        f":{db_config.get('password', 'postgres')}"
        f"@{db_config.get('host', 'localhost')}"
        f":{db_config.get('port', 5432)}"
        f"/{db_name}"
    )
    return normalize_database_url(raw, async_driver=async_driver)
