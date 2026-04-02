"""Generic BaseRepository providing standard CRUD operations."""

import logging
from typing import Any, Generic, TypeVar

from sqlalchemy import Select, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.repository.pk_strategy import PrimaryKeyStrategy, SinglePKStrategy
from core.repository.specification import PageRequest, PageResponse, SearchSpec

ModelT = TypeVar("ModelT")
logger = logging.getLogger(__name__)


class BaseRepository(Generic[ModelT]):
    """Base repository with generic CRUD operations.

    All methods receive session explicitly. Never creates session, never commits.
    """

    def __init__(self, model_class: type[ModelT]) -> None:
        self._model_class = model_class

    def _get_pk_strategy(self) -> PrimaryKeyStrategy:
        return SinglePKStrategy(self._default_pk_field())

    def _default_pk_field(self) -> str:
        return "id"

    def _get_searchable_fields(self) -> list[str]:
        """Override in subclass to define fields for text search."""
        return []

    # --- Read operations ---

    async def get_by_id(self, session: AsyncSession, pk_value: Any) -> ModelT | None:
        strategy = self._get_pk_strategy()
        stmt = select(self._model_class).where(
            strategy.build_where_clause(self._model_class, pk_value)  # type: ignore[arg-type]
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()  # type: ignore[return-value]

    async def exists(self, session: AsyncSession, pk_value: Any) -> bool:
        return await self.get_by_id(session, pk_value) is not None

    async def get_by_ids(self, session: AsyncSession, pk_values: list[Any]) -> list[ModelT]:
        pk_field = self._get_pk_strategy().get_unique_fields()[0]
        column = getattr(self._model_class, pk_field)
        stmt = select(self._model_class).where(column.in_(pk_values))
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def find_by(self, session: AsyncSession, **filters: Any) -> list[ModelT]:
        stmt = select(self._model_class)
        stmt = self._apply_kwargs_filters(stmt, filters)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def count_by(self, session: AsyncSession, **filters: Any) -> int:
        stmt = select(func.count()).select_from(self._model_class)
        stmt = self._apply_kwargs_filters(stmt, filters)
        result = await session.execute(stmt)
        return result.scalar_one()  # type: ignore[return-value]

    async def search_paged(
        self,
        session: AsyncSession,
        page: int = 1,
        size: int = 20,
        query: str | None = None,
        **filters: Any,
    ) -> tuple[list[ModelT], int]:
        """Paginated search with text search and exact filters."""
        stmt = select(self._model_class)
        count_stmt = select(func.count()).select_from(self._model_class)

        # Apply text search
        if query:
            search_conditions = self._build_text_search_filters(query)
            if search_conditions is not None:
                stmt = stmt.where(search_conditions)
                count_stmt = count_stmt.where(search_conditions)

        # Apply exact filters
        stmt = self._apply_kwargs_filters(stmt, filters)
        count_stmt = self._apply_kwargs_filters(count_stmt, filters)

        # Count
        total_result = await session.execute(count_stmt)
        total = total_result.scalar_one()  # type: ignore[assignment]

        # Apply sorting and pagination
        strategy = self._get_pk_strategy()
        stmt = stmt.order_by(*strategy.get_default_order_by(self._model_class))  # type: ignore[arg-type]
        stmt = stmt.offset((page - 1) * size).limit(size)

        result = await session.execute(stmt)
        items = list(result.scalars().all())
        return items, total

    async def search_with_spec(
        self,
        session: AsyncSession,
        spec: SearchSpec,
        pageable: PageRequest,
    ) -> PageResponse[ModelT]:
        """Search using specification pattern."""
        items, total = await self.search_paged(
            session,
            page=pageable.page,
            size=pageable.size,
            query=spec.query,
            **spec.filters,
        )
        return PageResponse.from_query_result(items, total, pageable.page, pageable.size)

    # --- Write operations ---

    async def create(self, session: AsyncSession, data: dict[str, Any] | ModelT) -> ModelT:
        if isinstance(data, dict):
            instance = self._model_class(**data)  # type: ignore[call-arg]
        else:
            instance = data
        session.add(instance)
        await session.flush()
        await session.refresh(instance)
        return instance

    async def update(
        self,
        session: AsyncSession,
        pk_value: Any,
        update_data: dict[str, Any],
    ) -> ModelT | None:
        instance = await self.get_by_id(session, pk_value)
        if instance is None:
            return None
        for key, value in update_data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        await session.flush()
        await session.refresh(instance)
        return instance

    async def delete(self, session: AsyncSession, pk_value: Any) -> bool:
        instance = await self.get_by_id(session, pk_value)
        if instance is None:
            return False
        await session.delete(instance)
        await session.flush()
        return True

    async def create_batch(self, session: AsyncSession, data_list: list[dict[str, Any]]) -> list[ModelT]:
        instances = [self._model_class(**data) for data in data_list]  # type: ignore[call-arg]
        session.add_all(instances)
        await session.flush()
        return instances

    async def delete_batch(self, session: AsyncSession, pk_values: list[Any]) -> int:
        pk_field = self._get_pk_strategy().get_unique_fields()[0]
        column = getattr(self._model_class, pk_field)
        stmt = delete(self._model_class).where(column.in_(pk_values))
        result = await session.execute(stmt)
        await session.flush()
        return result.rowcount  # type: ignore[return-value]

    # --- Internal helpers ---

    def _build_text_search_filters(self, query: str) -> Any | None:
        fields = self._get_searchable_fields()
        if not fields:
            return None
        conditions = []
        for field_name in fields:
            column = getattr(self._model_class, field_name, None)
            if column is not None:
                conditions.append(column.ilike(f"%{query}%"))
        return or_(*conditions) if conditions else None

    def _apply_kwargs_filters(self, stmt: Select[Any], filters: dict[str, Any]) -> Select[Any]:
        for key, value in filters.items():
            if value is None:
                continue
            if key.endswith("__in"):
                column_name = key[:-4]
                column = getattr(self._model_class, column_name, None)
                if column is not None:
                    stmt = stmt.where(column.in_(value))
            else:
                column = getattr(self._model_class, key, None)
                if column is not None:
                    stmt = stmt.where(column == value)
        return stmt
