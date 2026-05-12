"""Shared database URL resolver for runtime and Alembic."""

import os
from urllib.parse import urlsplit


def normalize_database_url(url: str) -> str:
    """Normalize Render/Postgres URLs to SQLAlchemy psycopg driver URLs."""
    value = url.strip()
    if not value:
        msg = "database url is empty"
        raise ValueError(msg)
    parsed = urlsplit(value)
    if parsed.scheme == "postgres":
        value = f"postgresql{value.removeprefix('postgres')}"
        parsed = urlsplit(value)
    if parsed.scheme == "postgresql":
        value = f"postgresql+psycopg{value.removeprefix('postgresql')}"
        parsed = urlsplit(value)
    if parsed.scheme != "postgresql+psycopg" or not parsed.netloc or not parsed.path.strip("/"):
        msg = "database url must be a postgresql URL with host and database name"
        raise ValueError(msg)
    return value


def resolve_database_url(config: dict[str, object], *, tenant: str = "default") -> str:
    """Resolve DATABASE_URL first, then fallback to existing YAML config."""
    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        return normalize_database_url(env_url)

    db_config = config.get("database", {})
    tenants = config.get("tenants", {})
    if not isinstance(db_config, dict) or not isinstance(tenants, dict):
        msg = "database config is invalid"
        raise ValueError(msg)

    tenant_config = tenants.get(tenant, {})
    if not isinstance(tenant_config, dict):
        tenant_config = {}
    tenant_database = tenant_config.get("database", {})
    if not isinstance(tenant_database, dict):
        tenant_database = {}
    db_name = str(tenant_database.get("name", "bedrock"))
    raw_url = (
        f"postgresql+psycopg://{db_config.get('username', 'postgres')}"
        f":{db_config.get('password', 'postgres')}"
        f"@{db_config.get('host', 'localhost')}"
        f":{db_config.get('port', 5432)}"
        f"/{db_name}"
    )
    return normalize_database_url(raw_url)
