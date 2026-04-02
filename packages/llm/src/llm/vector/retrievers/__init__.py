"""检索器模块。

提供多种检索模式的实现：
- PostgresVectorRetriever: 向量相似度检索
- PostgresFTSRetriever: 全文关键词检索
- HybridEnsembleRetriever: 混合检索（RRF 融合）
- create_retriever: 统一工厂函数
- RetrievalMode: 检索模式枚举
- RetrieverConfig: 检索器配置
"""

from llm.vector.retrievers.fts import PostgresFTSRetriever
from llm.vector.retrievers.hybrid import HybridEnsembleRetriever, RetrievalMode, RetrieverConfig, create_retriever
from llm.vector.retrievers.vector import PostgresVectorRetriever

__all__ = [
    "HybridEnsembleRetriever",
    "PostgresFTSRetriever",
    "PostgresVectorRetriever",
    "RetrievalMode",
    "RetrieverConfig",
    "create_retriever",
]
