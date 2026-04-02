"""Vector 模块 - 向量检索与存储服务。

提供统一的向量检索接口，支持多种检索模式：
- VECTOR_ONLY: 纯语义向量检索
- FTS_ONLY: 纯全文关键词检索
- HYBRID: 混合检索（RRF 融合）

核心组件：
- VectorStore: 向量存储服务（增删改查 + 相似度搜索）
- create_retriever: 检索器工厂函数
- HybridSearchConfig: 混合检索配置
- MetadataFilterBuilder: 元数据过滤器构建器（LangChain 标准）

模块结构（v2.0 重构后）：
- embeddings/: Embedding 提供商（DashScope、Volcengine）
- rerankers/: Reranker 提供商（异步实现）
- retrievers/: 检索器实现（Vector、FTS、Hybrid）
- store/: 向量存储核心
- fusion/: 融合策略
- mappers/: 数据映射
- services/: 业务服务
"""

# 从新模块结构导入
from llm.vector.embeddings import get_embedding_client
from llm.vector.fusion import FusionStrategy, HybridSearchConfig
from llm.vector.rerankers import get_reranker_client
from llm.vector.retrievers import RetrievalMode, RetrieverConfig, create_retriever
from llm.vector.store import MetadataFilterBuilder, VectorStore

__all__ = [
    "FusionStrategy",
    "HybridSearchConfig",
    "MetadataFilterBuilder",
    "RetrievalMode",
    "RetrieverConfig",
    "VectorStore",
    "create_retriever",
    "get_embedding_client",
    "get_reranker_client",
]
