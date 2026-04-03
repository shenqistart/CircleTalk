"""统一 API 响应封装。"""

from math import ceil
from typing import Any

from pydantic import BaseModel


class CommonResponse[T](BaseModel):
    """标准 API 响应信封。"""

    code: int = 200
    message: str = "success"
    data: T | None = None


def success_response(data: Any = None, message: str = "success") -> CommonResponse[Any]:  # noqa: ANN401
    return CommonResponse(code=200, message=message, data=data)


def error_response(message: str, code: int = 500) -> CommonResponse[None]:
    return CommonResponse(code=code, message=message, data=None)


def not_found_response(message: str = "Resource not found") -> CommonResponse[None]:
    return CommonResponse(code=404, message=message, data=None)


def bad_request_response(message: str) -> CommonResponse[None]:
    return CommonResponse(code=400, message=message, data=None)


def pageable_success_response(
    content: list[Any],
    total: int,
    page: int,
    size: int,
    message: str = "success",
) -> CommonResponse[dict[str, Any]]:
    """构建分页成功响应。"""
    return CommonResponse(
        code=200,
        message=message,
        data={
            "content": content,
            "total": total,
            "page": page,
            "size": size,
            "total_pages": ceil(total / size) if size > 0 else 0,
        },
    )
