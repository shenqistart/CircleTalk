"""
中文分词工具模块
使用jieba进行中文分词
"""

import warnings

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=UserWarning, message=".*pkg_resources is deprecated.*")
    import jieba

from core.logging import get_logger

logger = get_logger(__name__)


def tokenize(text: str) -> list[str]:
    """
    中文分词，返回词语列表

    Args:
        text: 待分词的文本

    Returns:
        分词结果列表
    """
    if not text or not text.strip():
        return []
    try:
        tokens = jieba.lcut(text.strip())
        return [token for token in tokens if token.strip()]
    except Exception:
        logger.exception("Tokenization failed, text: %s", text[:100])
        return text.strip().split()


__all__ = ["tokenize"]
