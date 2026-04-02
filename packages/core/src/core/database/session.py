"""Async database session management with multi-tenant schema isolation."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from core.context.request import try_current_tenant
from core.database.identifier import build_search_path_sql
from core.database.state import DatabaseRegistry

logger = logging.getLogger(__name__)


async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Async generator for HTTP/WebSocket request-scoped sessions.

    Automatically switches to tenant schema and manages transaction
    (begin -> commit on success, rollback on error).
    """
    factory = DatabaseRegistry.get_base_session_factory()
    async with factory() as session:
        tenant = try_current_tenant()
        if tenant:
            schema = DatabaseRegistry.get_schema_name(tenant)
            await session.execute(build_search_path_sql(schema))

        async with session.begin():
            yield session


@asynccontextmanager
async def scoped_session(tenant: str) -> AsyncGenerator[AsyncSession, None]:
    """Create an isolated session for background tasks / LangGraph nodes.

    Does NOT auto-commit. Write operations must explicitly call session.commit().
    """
    factory = DatabaseRegistry.get_base_session_factory()
    async with factory() as session:
        schema = DatabaseRegistry.get_schema_name(tenant)
        await session.execute(build_search_path_sql(schema))
        try:
            yield session
        finally:
            await session.close()
