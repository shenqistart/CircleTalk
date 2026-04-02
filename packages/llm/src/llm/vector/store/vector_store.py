"""VectorStore: 统一的向量存储服务（Schema 隔离模式）。

该服务直接使用SQLAlchemy和pgvector与数据库交互，
为上层业务提供了一个清晰、统一的接口来管理和检索向量化文档。
"""

from collections.abc import AsyncIterator, Mapping, Sequence
from contextlib import asynccontextmanager
from functools import cache
from typing import Any, cast, override

from core.app_config import core_config
from core.database import DatabaseRegistry
from core.database.identifier import build_search_path_sql
from core.logging import get_logger
from core.utils.text import tokenize_for_fts
from langchain_core.callbacks import Callbacks
from langchain_core.documents import Document
from langchain_core.documents.compressor import BaseDocumentCompressor
from langchain_core.retrievers import BaseRetriever
from pgvector.sqlalchemy import Vector
from sqlalchemy import ARRAY, Column, DateTime, MetaData, String, Table, Text, delete, func, select, text, type_coerce
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from llm.vector.embeddings import get_embedding_client
from llm.vector.rerankers import get_reranker_client
from llm.vector.retrievers import RetrievalMode, RetrieverConfig, create_retriever
from llm.vector.store.sqlalchemy_filters import SQLAlchemyFilterBuilder

logger = get_logger(__name__)
MetadataDict = dict[str, object]
FilterDict = dict[str, object]


def _normalize_document_metadata(doc: Document) -> MetadataDict:
    """LangChain Document.metadata 在类型系统中是 Any，这里显式标准化。"""
    raw_metadata = getattr(doc, "metadata", None)
    if isinstance(raw_metadata, Mapping):
        return dict(raw_metadata)
    return {}


def _row_metadata(raw_metadata: Mapping[str, object] | Sequence[tuple[str, object]] | None) -> MetadataDict:
    """将数据库查询返回的 JSONB 元数据转换为标准字典。"""
    if raw_metadata is None:
        return {}
    if isinstance(raw_metadata, Mapping):
        return dict(raw_metadata)
    return dict(raw_metadata)


@cache
def _get_table_for_collection(collection_name: str, vector_size: int) -> Table:
    """辅助函数，用于动态构建并缓存表的元数据对象。

    通过在代码中定义表结构，可以确保SQLAlchemy正确识别
    pgvector的VECTOR类型及其操作。
    """
    metadata = MetaData()
    return Table(
        collection_name,
        metadata,
        Column("id", String, primary_key=True),
        Column("content", Text, nullable=False),
        Column("embedding", cast(Any, Vector(vector_size)), nullable=False),
        Column("metadata", JSONB, nullable=False),
        Column("fts_document", TSVECTOR, nullable=True),
        Column("created_at", DateTime, nullable=False),
        Column("updated_at", DateTime, nullable=False),
    )


class VectorStore:
    """封装了向量存储操作的单例服务（Schema 隔离模式）。"""

    def __init__(self, registry: DatabaseRegistry) -> None:
        self._registry = registry
        logger.info("VectorStore initialized")

    @asynccontextmanager
    async def _create_session(self) -> AsyncIterator[AsyncSession]:
        """创建设置了租户 search_path 的 AsyncSession。

        Schema 隔离模式下，通过 SET search_path 实现租户数据隔离。

        Yields:
            设置了正确 search_path 的 AsyncSession
        """
        tenant = core_config.current_tenant_name
        schema = self._registry.get_schema_name(tenant)

        if not schema:
            logger.error("Schema not found: tenant=%s", tenant)
            msg = f"Schema for tenant '{tenant}' not found."
            raise RuntimeError(msg)

        session_factory = self._registry.get_base_session_factory()
        if not session_factory:
            msg = "Session factory not initialized"
            raise RuntimeError(msg)

        async with session_factory() as session:
            await session.execute(build_search_path_sql(schema))
            yield session

    async def add_documents(self, collection: str, documents: Sequence[Document], vector_size: int) -> None:
        """向指定的集合中添加或更新文档。

        通过从业务ID确定性地生成UUID，并使用UPSERT，该方法实现了幂等操作。
        fts_document 通过 unnest 批量 UPDATE 写入，避免 func 表达式在多行 VALUES 中的兼容性问题。
        """
        if not documents:
            logger.warning("Add skipped: collection=%s, reason=no_documents", collection)
            return
        embedding_client = get_embedding_client()
        text_batch = [doc.page_content for doc in documents]
        embeddings: list[list[float]] = await embedding_client.aembed_documents(text_batch)
        values_to_insert: list[dict[str, object]] = []
        tokenized_pairs: list[tuple[str, str]] = []
        for i, doc in enumerate(documents):
            metadata = _normalize_document_metadata(doc)
            doc_id_value = metadata.get("id")
            if doc_id_value is None:
                msg = "Document metadata 必须包含 'id' 字段"
                raise ValueError(msg)
            metadata_with_id = dict(metadata)
            doc_id_str = str(doc_id_value)
            metadata_with_id["id"] = doc_id_str
            tokenized_pairs.append((doc_id_str, tokenize_for_fts(doc.page_content)))
            values_to_insert.append(
                {
                    "id": doc_id_str,
                    "content": doc.page_content,
                    "embedding": embeddings[i],
                    "metadata": metadata_with_id,
                }
            )
        try:
            async with self._create_session() as session:
                table = _get_table_for_collection(collection, vector_size)
                stmt = pg_insert(table).values(values_to_insert)
                update_stmt = stmt.on_conflict_do_update(
                    index_elements=["id"],
                    set_={
                        "content": stmt.excluded.content,
                        "embedding": stmt.excluded.embedding,
                        "metadata": stmt.excluded.metadata,
                        "updated_at": text("CURRENT_TIMESTAMP"),
                    },
                )
                await session.execute(update_stmt)
                doc_ids = [pair[0] for pair in tokenized_pairs]
                tok_texts = [pair[1] for pair in tokenized_pairs]
                unnest_cte = select(
                    func.unnest(type_coerce(doc_ids, ARRAY(Text))).label("id"),
                    func.unnest(type_coerce(tok_texts, ARRAY(Text))).label("tok_text"),
                ).cte("fts_source")
                fts_update = (
                    table.update()
                    .where(table.c.id == unnest_cte.c.id)
                    .values(fts_document=func.to_tsvector("simple", unnest_cte.c.tok_text))
                )
                await session.execute(fts_update)
                await session.commit()
            logger.info("Documents upserted: collection=%s, count=%d", collection, len(documents))
        except Exception:
            logger.exception("Upsert failed: collection=%s", collection)
            raise

    async def delete_documents(self, collection: str, document_ids: list[str], vector_size: int) -> bool:
        """从指定的集合中删除文档。"""
        if not document_ids:
            logger.warning("Delete skipped: collection=%s, reason=no_document_ids", collection)
            return False
        ids_to_delete = [str(doc_id) for doc_id in document_ids]
        try:
            async with self._create_session() as session:
                table = _get_table_for_collection(collection, vector_size)
                stmt = delete(table).where(table.c.id.in_(ids_to_delete))
                await session.execute(stmt)
                await session.commit()
        except Exception:
            logger.exception("Delete failed: collection=%s", collection)
            raise
        else:
            logger.info("Documents deleted: collection=%s, count=%d", collection, len(document_ids))
            return True

    async def get_document_ids(self, collection: str, doc_filter: FilterDict, vector_size: int) -> list[str]:
        """根据元数据过滤器获取文档ID列表。"""
        async with self._create_session() as session:
            table = _get_table_for_collection(collection, vector_size)
            stmt = select(table.c.id)
            stmt = self._apply_metadata_filters(stmt, table, doc_filter)
            result = await session.execute(stmt)
            return [row[0] for row in result]

    def _apply_metadata_filters(self, stmt: Select, table: Table, filters: FilterDict | None) -> Select:
        """将元数据过滤器应用于SQLAlchemy查询语句。

        支持的操作符：
        - $and: 逻辑与 {"$and": [filter1, filter2]}
        - $or: 逻辑或 {"$or": [filter1, filter2]}
        - $in: 包含于列表 {"key": {"$in": [value1, value2]}}
        - $contains: 数组包含某个值 {"key": {"$contains": value}}
        - $overlap: 数组重叠（有交集）{"key": {"$overlap": [value1, value2]}}
        - 简单相等: {"key": value}
        """
        if not filters:
            return stmt
        builder = SQLAlchemyFilterBuilder(table)
        condition = builder.build_condition(filters)
        if condition is not None:
            stmt = stmt.where(condition)
        return stmt

    def _log_retriever_results(self, retriever_name: str, results: list[Document], query: str) -> None:
        """记录单个检索器的召回结果。"""
        logger.debug("Retriever results: query=%s, retriever=%s, count=%d", query, retriever_name, len(results))
        for i, doc in enumerate(results):
            metadata = _normalize_document_metadata(doc)
            score: object = metadata.get("relevance_score", "N/A")
            score_str: str = f"{score:.4f}" if isinstance(score, float) else str(score)
            doc_id: object = metadata.get("id", "N/A")
            logger.debug("  - %s %s: [分数: %s] - ID: %s", retriever_name, i + 1, score_str, doc_id)

    def _log_final_results(self, results: list[Document], collection: str, query: str, score_threshold: float) -> None:
        """记录重排序和过滤后的最终结果。"""
        logger.info("Final results: query=%s, collection=%s", query, collection)
        if not results:
            logger.info("No results found")
            return
        for i, doc in enumerate(results):
            metadata = _normalize_document_metadata(doc)
            relevance_raw = metadata.get("relevance_score", 0.0)
            relevance_score = (
                f"{float(relevance_raw):.4f}" if isinstance(relevance_raw, (int, float)) else str(relevance_raw)
            )
            doc_id: object = metadata.get("id", "N/A")
            logger.debug("Result %d: id=%s, score=%s", i + 1, doc_id, relevance_score)
        logger.info("Results filtered: threshold=%.2f, count=%d", score_threshold, len(results))

    async def fts_search(
        self,
        collection_name: str,
        query: str,
        k: int,
        vector_size: int,
        filters: FilterDict | None = None,
        score_threshold: float = 0.0,
        fts_config: str = "simple",
    ) -> list[Document]:
        """在 embedding 表上执行全文搜索。

        Args:
            collection_name: 目标集合名称。
            query: 原始查询文本（由 PostgreSQL parser 解析）。
            k: 返回的最大文档数量。
            vector_size: 向量维度（用于获取表定义）。
            filters: 元数据过滤器。
            score_threshold: 最低 ts_rank_cd 分数。
            fts_config: PostgreSQL regconfig。

        Returns:
            匹配的 Document 列表，按 ts_rank_cd 降序排列。
        """
        if not query:
            return []

        def _build_stmt(table: Table, ts_query_expr: Any) -> Select[Any]:
            rank_expr = func.ts_rank_cd(table.c.fts_document, ts_query_expr).label("rank")
            stmt = select(table.c.id, table.c.content, table.c.metadata, rank_expr).where(
                table.c.fts_document.op("@@")(ts_query_expr)
            )
            stmt = self._apply_metadata_filters(stmt, table, filters)
            if score_threshold > 0:
                stmt = stmt.where(rank_expr >= score_threshold)
            return stmt.order_by(rank_expr.desc()).limit(k)

        async def _execute_search(session: AsyncSession, table: Table, ts_query_expr: Any) -> list[Document]:
            result = await session.execute(_build_stmt(table, ts_query_expr))
            docs: list[Document] = []
            for row in result:
                metadata = _row_metadata(row.metadata)
                metadata["relevance_score"] = float(row.rank)
                metadata.setdefault("id", str(row.id))
                docs.append(Document(page_content=row.content, metadata=metadata))
            return docs

        async with self._create_session() as session:
            table = _get_table_for_collection(collection_name, vector_size)
            websearch_query = func.websearch_to_tsquery(fts_config, query)
            try:
                docs = await _execute_search(session, table, websearch_query)
            except DBAPIError:
                logger.warning(
                    "FTS websearch parser failed, fallback to plainto_tsquery: query='%s'",
                    query,
                    exc_info=True,
                )
                docs = []
            if docs:
                return docs

            plainto_query = func.plainto_tsquery(fts_config, query)
            return await _execute_search(session, table, plainto_query)

    async def similarity_search(
        self,
        collection_name: str,
        query: str,
        k: int,
        filters: FilterDict | None = None,
        score_threshold: float = 0.0,
    ) -> list[Document]:
        """执行纯向量相似度搜索，并根据分数阈值过滤结果。

        Args:
            collection_name: 目标集合的名称。
            query: 用于搜索的查询文本。
            k: 返回的最相似文档数量。
            filters: 应用于元数据的过滤器。
            score_threshold: 结果必须满足的最低相关性分数。

        Returns:
            一个包含Document对象的列表，按相关性从高到低排序。
        """
        vector_size = core_config.llm_vectors.dimensions
        embedding_client = get_embedding_client()
        query_embedding = await embedding_client.aembed_query(query)
        async with self._create_session() as session:
            table = _get_table_for_collection(collection_name, vector_size)
            stmt = select(
                table.c.id,
                table.c.content,
                table.c.metadata,
                table.c.embedding.cosine_distance(query_embedding).label("distance"),
            )
            stmt = self._apply_metadata_filters(stmt, table, filters)
            stmt = stmt.order_by(text("distance asc")).limit(k)
            result = await session.execute(stmt)
            docs: list[Document] = []
            for row in result:
                relevance_score = 1 - row.distance
                if relevance_score < score_threshold:
                    continue
                metadata = _row_metadata(row.metadata)
                metadata["relevance_score"] = relevance_score
                metadata.setdefault("id", str(row.id))
                docs.append(Document(page_content=row.content, metadata=metadata))
            return docs

    async def _rerank_and_filter_results(
        self, documents: list[Document], query: str, top_k: int, score_threshold: float
    ) -> list[Document]:
        """应用精排器和分数阈值过滤器。"""
        if not documents:
            return []
        reranker = get_reranker_client(top_k=top_k)
        final_filter = ThresholdFilter(score_threshold=score_threshold)
        reranked_results = await reranker.acompress_documents(documents=documents, query=query)
        final_results = await final_filter.acompress_documents(documents=list(reranked_results), query=query)
        return list(final_results)

    def create_retriever(self, mode: RetrievalMode, config: RetrieverConfig) -> BaseRetriever:
        """创建标准的LangChain Retriever实例。

        使用retriever_factory创建配置好的检索器，支持三种模式：
        - vector_only: 纯语义向量检索
        - fts_only: 纯全文关键词检索
        - hybrid: 混合检索（EnsembleRetriever + RRF）

        Args:
            mode: 检索模式
            config: 检索器配置

        Returns:
            配置好的BaseRetriever实例
        """
        return create_retriever(mode=mode, config=config)


class ThresholdFilter(BaseDocumentCompressor):
    """一个简单的文档压缩器，用于根据relevance_score进行阈值过滤。"""

    score_threshold: float

    @override
    async def acompress_documents(
        self, documents: Sequence[Document], query: str, callbacks: Callbacks | None = None
    ) -> list[Document]:
        """异步地根据阈值过滤文档。"""
        result: list[Document] = []
        for doc in documents:
            metadata = _normalize_document_metadata(doc)
            score = metadata.get("relevance_score", 0.0)
            if isinstance(score, (int, float)) and float(score) >= self.score_threshold:
                result.append(Document(page_content=doc.page_content, metadata=metadata))
        return result

    @override
    def compress_documents(
        self, documents: Sequence[Document], query: str, callbacks: Callbacks | None = None
    ) -> list[Document]:
        """同步地根据阈值过滤文档。"""
        result: list[Document] = []
        for doc in documents:
            metadata = _normalize_document_metadata(doc)
            score = metadata.get("relevance_score", 0.0)
            if isinstance(score, (int, float)) and float(score) >= self.score_threshold:
                result.append(Document(page_content=doc.page_content, metadata=metadata))
        return result
