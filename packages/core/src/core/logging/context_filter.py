"""请求上下文日志过滤器.

自动将 request_id 从 RequestContext 注入到所有日志记录中。
"""

import logging
import warnings
from contextvars import ContextVar
from typing import cast

from core.context.request import RequestContext

__all__ = ["RequestContextFilter"]

DEFAULT_REQUEST_ID = "-"


class RequestContextFilter(logging.Filter):
    """请求上下文日志过滤器.

    从 ContextVar 中提取 request_id，注入到 LogRecord。
    如果上下文不存在或 request_id 为空，使用默认值 "-"。

    Usage:
        handler.addFilter(RequestContextFilter())
    """

    _context_var_cache: ContextVar[RequestContext | None] | None = None

    @classmethod
    def _get_request_context(cls) -> RequestContext | None:
        """安全获取 RequestContext（延迟绑定）."""
        if cls._context_var_cache is None:
            try:
                from core.context.request import (  # noqa: PLC0415
                    _request_context,
                )

                cls._context_var_cache = cast(
                    ContextVar["RequestContext | None"],
                    _request_context,
                )
            except ImportError:
                warnings.warn(
                    "RequestContextFilter: 无法导入 _request_context，request_id 将始终为默认值",
                    RuntimeWarning,
                    stacklevel=2,
                )
                return None

        try:
            return cls._context_var_cache.get()
        except Exception:
            return None

    def filter(self, record: logging.LogRecord) -> bool:
        """过滤并注入 request_id."""
        try:
            ctx = self._get_request_context()
            request_id = ctx.request_id if ctx and ctx.request_id else DEFAULT_REQUEST_ID
        except Exception:
            request_id = DEFAULT_REQUEST_ID
        record.request_id = request_id
        return True
