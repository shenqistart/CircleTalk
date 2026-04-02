"""Query specification pattern: SearchSpec, PageRequest, PageResponse."""

from dataclasses import dataclass, field
from math import ceil
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass
class SearchSpec:
    """Query specification for filtering and searching."""

    filters: dict[str, Any] = field(default_factory=dict)
    query: str | None = None
    order_by: list[str] = field(default_factory=list)


@dataclass
class PageRequest:
    """Pagination request parameters."""

    page: int = 1
    size: int = 20
    sort: list[tuple[str, str]] | None = None

    def __post_init__(self) -> None:
        if self.page < 1:
            self.page = 1
        if self.size < 1:
            self.size = 1
        if self.size > 1000:
            self.size = 1000

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


@dataclass
class PageResponse(Generic[T]):
    """Paginated response wrapper."""

    content: list[T]
    page: int
    size: int
    total: int

    @property
    def total_pages(self) -> int:
        return ceil(self.total / self.size) if self.size > 0 else 0

    @classmethod
    def from_query_result(
        cls,
        content: list[T],
        total: int,
        page: int,
        size: int,
    ) -> "PageResponse[T]":
        return cls(content=content, page=page, size=size, total=total)
