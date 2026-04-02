"""
核心文件操作工具。
"""

import logging
import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

logger = logging.getLogger(__name__)


@contextmanager
def temporary_file(suffix: str = "", prefix: str = "tmp") -> Generator[str]:
    """
    安全的临时文件上下文管理器，确保文件在退出时清理。

    Args:
        suffix: 文件后缀
        prefix: 文件前缀

    Yields:
        临时文件路径
    """
    temp_path = ""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix=prefix) as temp_file:
            temp_path = temp_file.name
        yield temp_path
    finally:
        if temp_path:
            try:
                Path(temp_path).unlink(missing_ok=True)
            except Exception as exc:
                logger.warning("临时文件清理失败: %s, 错误: %s", temp_path, exc)


def get_file_extension(filename: str) -> str:
    """
    获取文件扩展名（小写，带点）。
    """
    return Path(filename or "").suffix.lower()


__all__ = ["get_file_extension", "temporary_file"]
