"""性能计时工具.

提供同步和异步上下文管理器和装饰器，用于统一的性能日志记录。
支持慢查询自动告警（超过阈值升级为 WARNING）。
"""

from __future__ import annotations

import functools
import time
from collections.abc import AsyncIterator, Awaitable, Callable, Iterator
from contextlib import asynccontextmanager, contextmanager
from logging import Logger
from typing import Any, ParamSpec, TypeVar

from core.logging.config import LogConfig
from core.logging.core import get_logger

__all__ = [
    "alog_timing",
    "atimed",
    "log_timing",
    "timed",
]

P = ParamSpec("P")
R = TypeVar("R")


def _timing_core(
    threshold: int,
    start_time: float,
    operation: str,
    logger: Logger,
    prefix: str,
    extra_dict: dict[str, Any],
    success: bool,
    error: Exception | None = None,
) -> int:
    """统一的计时日志记录逻辑.

    Args:
        threshold: 慢查询阈值（毫秒）
        start_time: 操作开始时间（perf_counter）
        operation: 操作描述
        logger: Logger 实例
        prefix: 日志前缀
        extra_dict: 额外的日志字段
        success: 操作是否成功
        error: 异常对象（仅在 success=False 时有效）

    Returns:
        操作耗时（毫秒）
    """
    duration_ms = int((time.perf_counter() - start_time) * 1000)
    if success:
        level = "warning" if duration_ms >= threshold else "info"
        suffix = " (slow)" if duration_ms >= threshold else ""
        _log_with_extra(logger, level, prefix, f"{operation} done{suffix}", duration_ms, extra_dict)
    else:
        _log_with_extra(
            logger,
            "warning",
            prefix,
            f"{operation} failed",
            duration_ms,
            {**extra_dict, "error": str(error)},
        )
    return duration_ms


def _get_threshold(operation_type: str | None) -> int:
    """获取操作类型对应的慢查询阈值."""
    thresholds = LogConfig.SLOW_THRESHOLDS
    if operation_type and operation_type.lower() in thresholds:
        return thresholds[operation_type.lower()]
    return thresholds["default"]


@asynccontextmanager
async def alog_timing(
    logger_name: str,
    operation: str,
    *,
    prefix: str = "",
    extra: dict[str, Any] | None = None,
    warn_threshold_ms: int | None = None,
    operation_type: str | None = None,
) -> AsyncIterator[None]:
    """异步性能计时上下文管理器.

    Args:
        logger_name: Logger 名称（通常使用 __name__）
        operation: 操作描述
        prefix: 日志前缀（如 "[CUBE]"、"[LLM]"）
        extra: 额外的日志字段（key=value 格式输出）
        warn_threshold_ms: 慢查询阈值（毫秒），超过则升级为 WARNING
        operation_type: 操作类型（用于自动获取阈值：http/db/llm/cube/vector）

    Yields:
        None

    Examples:
        >>> async with alog_timing(__name__, "Cube query", prefix="[CUBE]", extra={"view": "SalesOverview"}):
        ...     result = await client.load(query)
    """
    logger = get_logger(logger_name)
    extra_dict = extra or {}
    start_time = time.perf_counter()

    # 确定阈值
    threshold = warn_threshold_ms if warn_threshold_ms is not None else _get_threshold(operation_type)

    try:
        yield
    except Exception as e:
        _timing_core(threshold, start_time, operation, logger, prefix, extra_dict, success=False, error=e)
        raise
    else:
        _timing_core(threshold, start_time, operation, logger, prefix, extra_dict, success=True)


def _log_with_extra(
    logger: Logger,
    level: str,
    prefix: str,
    message: str,
    duration_ms: int,
    extra: dict[str, Any],
) -> None:
    """格式化并输出日志."""
    log_func = getattr(logger, level)
    parts = [f"duration={duration_ms}ms"]
    for key, value in extra.items():
        parts.append(f"{key}={value}")

    full_prefix = f"{prefix} " if prefix else ""
    log_func("%s%s: %s", full_prefix, message, ", ".join(parts))


def atimed(
    *,
    prefix: str = "",
    operation: str | None = None,
    warn_threshold_ms: int | None = None,
    operation_type: str | None = None,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """异步性能计时装饰器.

    Args:
        prefix: 日志前缀（如 "[CUBE]"、"[LLM]"）
        operation: 操作描述（默认使用函数名）
        warn_threshold_ms: 慢查询阈值（毫秒），超过则升级为 WARNING
        operation_type: 操作类型（用于自动获取阈值：http/db/llm/cube/vector）

    Returns:
        装饰后的异步函数

    Examples:
        >>> @atimed(prefix="[LLM]", operation="Chat completion", warn_threshold_ms=5000)
        ... async def chat(self, messages): ...
    """

    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        op_name = operation or func.__name__

        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            async with alog_timing(
                func.__module__,
                op_name,
                prefix=prefix,
                warn_threshold_ms=warn_threshold_ms,
                operation_type=operation_type,
            ):
                return await func(*args, **kwargs)

        return wrapper

    return decorator


@contextmanager
def log_timing(
    logger_name: str,
    operation: str,
    *,
    prefix: str = "",
    extra: dict[str, Any] | None = None,
    warn_threshold_ms: int | None = None,
    operation_type: str | None = None,
) -> Iterator[None]:
    """同步性能计时上下文管理器.

    Args:
        logger_name: Logger 名称（通常使用 __name__）
        operation: 操作描述
        prefix: 日志前缀（如 "[CUBE]"、"[LLM]"）
        extra: 额外的日志字段（key=value 格式输出）
        warn_threshold_ms: 慢查询阈值（毫秒），超过则升级为 WARNING
        operation_type: 操作类型（用于自动获取阈值：http/db/llm/cube/vector）

    Yields:
        None

    Examples:
        >>> with log_timing(__name__, "Database query", prefix="[DB]", operation_type="db"):
        ...     result = execute_query()
    """
    logger = get_logger(logger_name)
    extra_dict = extra or {}
    start_time = time.perf_counter()

    threshold = warn_threshold_ms if warn_threshold_ms is not None else _get_threshold(operation_type)

    try:
        yield
    except Exception as e:
        _timing_core(threshold, start_time, operation, logger, prefix, extra_dict, success=False, error=e)
        raise
    else:
        _timing_core(threshold, start_time, operation, logger, prefix, extra_dict, success=True)


def timed(
    *,
    prefix: str = "",
    operation: str | None = None,
    warn_threshold_ms: int | None = None,
    operation_type: str | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """同步性能计时装饰器.

    Args:
        prefix: 日志前缀（如 "[CUBE]"、"[LLM]"）
        operation: 操作描述（默认使用函数名）
        warn_threshold_ms: 慢查询阈值（毫秒），超过则升级为 WARNING
        operation_type: 操作类型（用于自动获取阈值：http/db/llm/cube/vector）

    Returns:
        装饰后的同步函数

    Examples:
        >>> @timed(prefix="[DB]", operation="Database query", operation_type="db")
        ... def query_database(self, query): ...
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        op_name = operation or func.__name__

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with log_timing(
                func.__module__,
                op_name,
                prefix=prefix,
                warn_threshold_ms=warn_threshold_ms,
                operation_type=operation_type,
            ):
                return func(*args, **kwargs)

        return wrapper

    return decorator
