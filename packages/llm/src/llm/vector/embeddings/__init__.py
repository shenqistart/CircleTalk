"""Embedding 提供商模块。

提供统一的 Embedding 接口和多提供商实现：
- BaseAsyncEmbeddings: 异步 Embedding 基类
- DashScopeEmbeddings: 阿里云 DashScope 实现
- VolcengineEmbeddings: 火山引擎实现
- get_embedding_client: 工厂函数
"""

from llm.vector.embeddings.base import BaseAsyncEmbeddings
from llm.vector.embeddings.dashscope import DashScopeEmbeddings
from llm.vector.embeddings.factory import get_embedding_client
from llm.vector.embeddings.volcengine import VolcengineEmbeddings

__all__ = [
    "BaseAsyncEmbeddings",
    "DashScopeEmbeddings",
    "VolcengineEmbeddings",
    "get_embedding_client",
]
