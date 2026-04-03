"""FastAPI 查询参数与响应的分页模型。"""

from math import ceil
from typing import Any

from fastapi import Query
from pydantic import BaseModel


class PageParams:
    """FastAPI Depends 分页查询参数类。"""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="页码"),
        size: int = Query(10, ge=1, le=100, description="每页条数"),
    ) -> None:
        self.page = page
        self.size = size


class PageResult[T](BaseModel):
    """通用分页响应模型。"""

    content: list[T]
    total: int
    page: int
    size: int
    total_pages: int

    @classmethod
    def create(
        cls,
        content: list[Any],
        total: int,
        page: int,
        size: int,
    ) -> "PageResult[Any]":
        return cls(
            content=content,
            total=total,
            page=page,
            size=size,
            total_pages=ceil(total / size) if size > 0 else 0,
        )
