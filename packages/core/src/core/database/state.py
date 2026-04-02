"""Database engine and session factory registry for multi-tenant support."""

from typing import ClassVar

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker


class DatabaseRegistry:
    """Multi-tenant database resource registry (schema isolation mode).

    Manages shared engine, base session factory, and tenant-to-schema mapping.
    """

    _shared_engine: ClassVar[AsyncEngine | None] = None
    _base_session_factory: ClassVar[async_sessionmaker[AsyncSession] | None] = None
    _schema_mapping: ClassVar[dict[str, str]] = {}

    @classmethod
    def register_shared_engine(
        cls,
        engine: AsyncEngine,
        factory: async_sessionmaker[AsyncSession],
    ) -> None:
        cls._shared_engine = engine
        cls._base_session_factory = factory

    @classmethod
    def register_tenant_schema(cls, tenant: str, schema: str) -> None:
        cls._schema_mapping[tenant] = schema

    @classmethod
    def get_schema_name(cls, tenant: str) -> str:
        schema = cls._schema_mapping.get(tenant)
        if schema is None:
            msg = f"Unknown tenant: {tenant}. Registered: {list(cls._schema_mapping.keys())}"
            raise ValueError(msg)
        return schema

    @classmethod
    def get_engine(cls) -> AsyncEngine:
        if cls._shared_engine is None:
            msg = "Database engine not initialized. Call initialize_db_engines() first."
            raise RuntimeError(msg)
        return cls._shared_engine

    @classmethod
    def get_base_session_factory(cls) -> async_sessionmaker[AsyncSession]:
        if cls._base_session_factory is None:
            msg = "Session factory not initialized."
            raise RuntimeError(msg)
        return cls._base_session_factory

    @classmethod
    def schema_mapping(cls) -> dict[str, str]:
        return dict(cls._schema_mapping)

    @classmethod
    def clear(cls) -> None:
        cls._shared_engine = None
        cls._base_session_factory = None
        cls._schema_mapping.clear()


database_registry = DatabaseRegistry()
