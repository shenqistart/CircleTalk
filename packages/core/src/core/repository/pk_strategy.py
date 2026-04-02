"""主键策略：支持单一主键和复合主键的 BaseRepository 适配。"""

from typing import Any, Protocol, Sequence

from sqlalchemy import ColumnElement, and_
from sqlalchemy.orm import DeclarativeBase

# 主键值类型：标量或元组（复合主键）
PrimaryKeyScalar = str | int
PrimaryKeyValue = PrimaryKeyScalar | tuple[PrimaryKeyScalar, ...]


class PrimaryKeyStrategy(Protocol):
    """Unified interface for primary key operations."""

    def build_where_clause(self, model: type[DeclarativeBase], pk_value: Any) -> ColumnElement[bool]: ...
    def extract_pk_value(self, instance: DeclarativeBase) -> Any: ...
    def get_unique_fields(self) -> list[str]: ...
    def get_default_order_by(self, model: type[DeclarativeBase]) -> list[ColumnElement[Any]]: ...


class SinglePKStrategy:
    """Strategy for models with a single primary key field (default: 'id')."""

    def __init__(self, pk_field: str = "id") -> None:
        self.pk_field = pk_field

    def build_where_clause(self, model: type[DeclarativeBase], pk_value: Any) -> ColumnElement[bool]:
        column = getattr(model, self.pk_field)
        if isinstance(pk_value, (list, tuple)):
            msg = f"SinglePKStrategy expects scalar value, got {type(pk_value)}"
            raise TypeError(msg)
        return column == pk_value  # type: ignore[return-value]

    def extract_pk_value(self, instance: DeclarativeBase) -> Any:
        return getattr(instance, self.pk_field)

    def get_unique_fields(self) -> list[str]:
        return [self.pk_field]

    def get_default_order_by(self, model: type[DeclarativeBase]) -> list[ColumnElement[Any]]:
        return [getattr(model, self.pk_field).desc()]


class CompositePKStrategy:
    """Strategy for models with composite primary keys."""

    def __init__(self, pk_fields: Sequence[str]) -> None:
        if len(pk_fields) < 2:
            msg = "CompositePKStrategy requires at least 2 fields"
            raise ValueError(msg)
        self.pk_fields = list(pk_fields)

    def build_where_clause(self, model: type[DeclarativeBase], pk_value: Any) -> ColumnElement[bool]:
        if not isinstance(pk_value, (list, tuple)) or len(pk_value) != len(self.pk_fields):
            msg = f"Expected tuple of {len(self.pk_fields)} values"
            raise TypeError(msg)
        conditions = [
            getattr(model, field) == value
            for field, value in zip(self.pk_fields, pk_value, strict=True)
        ]
        return and_(*conditions)

    def extract_pk_value(self, instance: DeclarativeBase) -> tuple[Any, ...]:
        return tuple(getattr(instance, field) for field in self.pk_fields)

    def get_unique_fields(self) -> list[str]:
        return list(self.pk_fields)

    def get_default_order_by(self, model: type[DeclarativeBase]) -> list[ColumnElement[Any]]:
        return [getattr(model, self.pk_fields[0]).desc()]
