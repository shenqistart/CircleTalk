"""统一日志模块.

提供完整的日志记录功能，包括：
- 主日志系统（configure_logging, get_logger, log_response）
- 早期启动日志（get_import_logger, get_bootstrap_logger, get_lifespan_logger）
- 性能计时工具（alog_timing, atimed, log_timing, timed）
- 辅助工具（TqdmToLogger）

Usage:
    # 主日志功能
    from core.logging import configure_logging, get_logger

    configure_logging(level="INFO", console_output=True, colored_output=True)
    logger = get_logger(__name__)
    logger.info("Application started")

    # 早期启动日志
    from core.logging import get_import_logger

    _import_logger = get_import_logger()
    _import_logger.info("Loading modules...")

    # 异步性能计时
    from core.logging import alog_timing, atimed

    async with alog_timing(__name__, "Cube query", prefix="[CUBE]"):
        result = await client.load(query)

    @atimed(prefix="[LLM]", operation="Chat completion", warn_threshold_ms=5000)
    async def chat(messages):
        ...

    # 同步性能计时
    from core.logging import log_timing, timed

    with log_timing(__name__, "Database query", prefix="[DB]", operation_type="db"):
        result = execute_query()

    @timed(prefix="[DB]", operation="Database query", operation_type="db")
    def query_database(query):
        ...

    # 辅助工具
    from core.logging import TqdmToLogger

    tqdm_logger = TqdmToLogger(logger)
"""

from __future__ import annotations

from core.logging.config import LogConfig, TqdmToLogger
from core.logging.context_filter import RequestContextFilter
from core.logging.core import configure_logging, get_logger, get_startup_logger, log_response
from core.logging.early import get_bootstrap_logger, get_import_logger, get_lifespan_logger
from core.logging.state import LoggingPhase, get_logging_phase, is_early_configured, is_fully_configured
from core.logging.timing import alog_timing, atimed, log_timing, timed

__all__ = [
    "LogConfig",
    "LoggingPhase",
    "RequestContextFilter",
    "TqdmToLogger",
    "alog_timing",
    "atimed",
    "configure_logging",
    "get_bootstrap_logger",
    "get_import_logger",
    "get_lifespan_logger",
    "get_logger",
    "get_logging_phase",
    "get_startup_logger",
    "is_early_configured",
    "is_fully_configured",
    "log_response",
    "log_timing",
    "timed",
]
