"""PostgreSQL SQL identifier safety utilities."""

from psycopg import sql as psycopg_sql
from sqlalchemy import TextClause, text


def build_search_path_sql(schema: str) -> TextClause:
    """Build safe SET search_path statement using psycopg.sql.Identifier."""
    stmt = psycopg_sql.SQL("SET search_path TO {schema}").format(
        schema=psycopg_sql.Identifier(schema)
    )
    return text(stmt.as_string(None))  # type: ignore[arg-type]


def build_create_schema_sql(schema: str) -> TextClause:
    """Build safe CREATE SCHEMA IF NOT EXISTS statement."""
    stmt = psycopg_sql.SQL("CREATE SCHEMA IF NOT EXISTS {schema}").format(
        schema=psycopg_sql.Identifier(schema)
    )
    return text(stmt.as_string(None))  # type: ignore[arg-type]
