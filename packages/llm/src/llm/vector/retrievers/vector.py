"""PostgresVectorRetriever: 基于 LangChain BaseRetriever 接口的向量相似度检索器。

提供标准的向量语义检索功能，可与 PostgresFTSRetriever 组合使用（通过 EnsembleRetriever）。
"""

from typing import Any

from core.logging import get_logger
from langchain_core.callbacks import AsyncCallbackManagerForRetrieverRun, CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import ConfigDict

logger = get_logger(__name__)


class PostgresVectorRetriever(BaseRetriever):
    """PostgreSQL 向量相似度检索器。

    基于 pgvector 实现语义相似度检索，使用 cosine distance 度量。
    实现了 LangChain 的 BaseRetriever 接口，可与其他检索器组合使用。

    特性：
    - 向量相似度检索（cosine distance）
    - 元数据过滤支持
    - 分数阈值过滤
    - 可与 PostgresFTSRetriever 配对使用（通过 EnsembleRetriever）

    使用示例：
        vector_retriever = PostgresVectorRetriever(
            vector_store=vector_store,
            collection_name="knowledge_chunks_embedding",
            vector_size=1024,
            k=5,
            score_threshold=0.0,
            filters={"category": "产品手册"}
        )
        results = await vector_retriever.ainvoke("如何使用产品？")
    """

    vector_store: Any
    collection_name: str
    vector_size: int
    k: int = 5
    score_threshold: float = 0.0
    filters: dict[str, Any] | None = None
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def _get_relevant_documents(self, query: str, *, run_manager: CallbackManagerForRetrieverRun) -> list[Document]:
        """同步版本接口（不支持）。"""
        msg = "PostgresVectorRetriever 不支持同步获取文档。"
        raise NotImplementedError(msg)

    async def _aget_relevant_documents(
        self, query: str, *, run_manager: AsyncCallbackManagerForRetrieverRun
    ) -> list[Document]:
        """异步地从向量存储检索相似文档。

        Args:
            query: 查询文本
            run_manager: LangChain回调管理器（接口规范要求，当前未使用）

        Returns:
            相似文档列表，按相关性降序排列
        """
        _ = run_manager  # 接口规范要求的参数，保留以符合 LangChain BaseRetriever 接口
        logger.debug("向量检索: query='%s', k=%s, threshold=%s", query, self.k, self.score_threshold)
        results = await self.vector_store.similarity_search(
            collection_name=self.collection_name,
            query=query,
            k=self.k,
            filters=self.filters,
            score_threshold=self.score_threshold,
        )
        logger.debug("向量检索完成，返回 %s 个文档", len(results))
        return results
