"""LangSmith 可观测性集成.

支持两种配置方式（优先级从高到低）：

1. config.yaml:
   langsmith:
     enabled: true
     api_key: ls-xxx
     project: bedrock
     endpoint: https://api.smith.langchain.com

2. 环境变量:
   LANGSMITH_TRACING=true
   LANGSMITH_API_KEY=ls-xxx
   LANGSMITH_PROJECT=bedrock
   LANGSMITH_ENDPOINT=https://api.smith.langchain.com
"""

from __future__ import annotations

import importlib
import os
from functools import lru_cache

from core.app_config import core_config
from core.logging import get_logger

logger = get_logger(__name__)


def _parse_bool_env(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_langsmith_config() -> tuple[bool, str, str, str]:
    """获取 LangSmith 配置（优先 config.yaml，其次环境变量）.

    Returns:
        (enabled, api_key, project, endpoint)
    """
    try:
        if core_config.is_initialized():
            cfg = core_config.langsmith
            if cfg.enabled and cfg.api_key:
                return True, cfg.api_key, cfg.project, cfg.endpoint
    except Exception:
        logger.debug("配置未初始化，回退到环境变量")

    env_enabled = _parse_bool_env(os.getenv("LANGSMITH_TRACING"))
    api_key = os.getenv("LANGSMITH_API_KEY", "")
    project = os.getenv("LANGSMITH_PROJECT", "")
    endpoint = os.getenv("LANGSMITH_ENDPOINT", "")
    enabled = bool(env_enabled and api_key)
    return enabled, api_key, project, endpoint


def _validate_langsmith_installation() -> bool:
    try:
        importlib.import_module("langsmith")
    except ImportError:
        logger.warning("langsmith 包未安装，无法启用追踪")
        return False
    return True


@lru_cache(maxsize=1)
def configure_langsmith_tracing() -> bool:
    """配置 LangSmith 追踪环境变量（单例）.

    Returns:
        True 表示已启用 LangSmith 追踪，否则 False
    """
    enabled, api_key, project, endpoint = _get_langsmith_config()
    if not enabled:
        logger.debug("LangSmith not configured, skipping initialization")
        return False
    if not _validate_langsmith_installation():
        return False

    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = api_key
    if project:
        os.environ["LANGSMITH_PROJECT"] = project
    if endpoint:
        os.environ["LANGSMITH_ENDPOINT"] = endpoint

    logger.info(
        "LangSmith 追踪已启用 (project=%s, endpoint=%s)",
        project or "-",
        endpoint or "default",
    )
    return True


__all__ = ["configure_langsmith_tracing"]
