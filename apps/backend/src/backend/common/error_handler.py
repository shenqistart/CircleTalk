"""API 端点异常处理装饰器。"""

import logging
from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from fastapi import HTTPException

from backend.common.response import CommonResponse, error_response

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


def error_handler(
    operation: str,
) -> Callable[
    [Callable[P, Coroutine[Any, Any, R]]],
    Callable[P, Coroutine[Any, Any, R]],
]:
    """将异常转换为 HTTPException 的装饰器。"""

    def decorator(
        func: Callable[P, Coroutine[Any, Any, R]],
    ) -> Callable[P, Coroutine[Any, Any, R]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except ValueError as e:
                logger.warning("%s failed: %s", operation, e)
                raise HTTPException(status_code=400, detail=str(e)) from e
            except Exception as e:
                logger.exception("%s error", operation)
                raise HTTPException(status_code=500, detail=f"{operation}失败") from e

        return wrapper

    return decorator


def response_error_handler(
    operation: str,
) -> Callable[
    [Callable[P, Coroutine[Any, Any, CommonResponse[Any]]]],
    Callable[P, Coroutine[Any, Any, CommonResponse[Any]]],
]:
    """将异常转换为 CommonResponse 错误格式的装饰器。"""

    def decorator(
        func: Callable[P, Coroutine[Any, Any, CommonResponse[Any]]],
    ) -> Callable[P, Coroutine[Any, Any, CommonResponse[Any]]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> CommonResponse[Any]:
            try:
                return await func(*args, **kwargs)
            except ValueError as e:
                logger.warning("%s failed: %s", operation, e)
                return error_response(str(e), code=400)
            except Exception:
                logger.exception("%s error", operation)
                return error_response(f"{operation}失败")

        return wrapper

    return decorator
