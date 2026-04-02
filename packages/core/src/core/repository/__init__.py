"""Repository infrastructure: generic CRUD, PK strategies, query specifications."""

from core.repository.base_repository import BaseRepository
from core.repository.pk_strategy import CompositePKStrategy, PrimaryKeyValue, SinglePKStrategy
from core.repository.specification import PageRequest, PageResponse, SearchSpec

__all__ = [
    "BaseRepository",
    "CompositePKStrategy",
    "PrimaryKeyValue",
    "PageRequest",
    "PageResponse",
    "SearchSpec",
    "SinglePKStrategy",
]
