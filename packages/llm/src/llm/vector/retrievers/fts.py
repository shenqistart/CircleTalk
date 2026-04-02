"""PostgresFTSRetriever: 基于 embedding 表 fts_document 列的全文搜索检索器。"""

from typing import Any

from core.logging import get_logger
from core.utils.text import tokenize_for_fts
from langchain_core.callbacks import AsyncCallbackManagerForRetrieverRun, CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import ConfigDict

logger = get_logger(__name__)


class PostgresFTSRetriever(BaseRetriever):
    """基于 embedding 表 fts_document 列的 LangChain FTS 检索器。

    与 PostgresVectorRetriever 对称设计，通过 VectorStore.fts_search() 执行查询，
    元数据直接来自 embedding 表的 JSONB metadata 列，保证与向量检索一致。
    """

    vector_store: Any
    collection_name: str
    vector_size: int
    k: int = 5
    score_threshold: float = 0.0
    filters: dict[str, Any] | None = None
    fts_config: str = "simple"
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def _get_relevant_documents(self, query: str, *, run_manager: CallbackManagerForRetrieverRun) -> list[Document]:
        msg = "PostgresFTSRetriever 不支持同步获取文档。"
        raise NotImplementedError(msg)

    def _build_processed_query(self, query: str) -> str:
        """对原始查询做分词与清洗，返回可直接给 PostgreSQL parser 的查询文本。"""
        tokenized_query = tokenize_for_fts(query).strip()
        if tokenized_query:
            return tokenized_query
        return query.strip()

    async def _aget_relevant_documents(
        self, query: str, *, run_manager: AsyncCallbackManagerForRetrieverRun
    ) -> list[Document]:
        """异步地从 embedding 表执行全文搜索。

        Args:
            query: 查询文本
            run_manager: LangChain 回调管理器（接口规范要求）
        """
        _ = run_manager
        processed_query = self._build_processed_query(query)
        if not processed_query:
            logger.warning("Query '%s' produced empty tsquery after tokenization, skipping FTS", query)
            return []

        logger.debug("FTS search: query='%s', processed='%s', k=%s", query, processed_query, self.k)
        results = await self.vector_store.fts_search(
            collection_name=self.collection_name,
            query=processed_query,
            k=self.k,
            vector_size=self.vector_size,
            filters=self.filters,
            score_threshold=self.score_threshold,
            fts_config=self.fts_config,
        )
        logger.debug("FTS search completed, returned %s documents", len(results))
        return results
