"""日志系统生命周期状态管理.

统一管理早期日志和主日志系统的状态，避免状态分散在多个模块中。
"""

from __future__ import annotations

from enum import Enum

__all__ = ["LoggingPhase", "get_logging_phase", "is_early_configured", "is_fully_configured", "set_logging_phase"]


class LoggingPhase(Enum):
    """日志系统生命周期阶段."""

    UNINITIALIZED = "uninitialized"  # 未初始化
    EARLY = "early"  # 早期日志（启动阶段）
    CONFIGURED = "configured"  # 主日志系统已配置


class _LoggingState:
    """日志系统状态管理（单例模式）."""

    def __init__(self) -> None:
        self.phase: LoggingPhase = LoggingPhase.UNINITIALIZED


_state = _LoggingState()


def get_logging_phase() -> LoggingPhase:
    """获取当前日志系统阶段."""
    return _state.phase


def set_logging_phase(phase: LoggingPhase) -> None:
    """设置日志系统阶段.

    Args:
        phase: 目标阶段
    """
    _state.phase = phase


def is_early_configured() -> bool:
    """检查早期日志是否已配置."""
    return _state.phase in (LoggingPhase.EARLY, LoggingPhase.CONFIGURED)


def is_fully_configured() -> bool:
    """检查主日志系统是否已配置."""
    return _state.phase == LoggingPhase.CONFIGURED
