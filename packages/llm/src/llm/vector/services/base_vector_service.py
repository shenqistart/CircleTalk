"""BaseVectorService: 提供与向量数据库同步的通用服务基类。"""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any, cast

from core.app_config import VectorCollectionKey, core_config
from core.database import Base
from core.repository.base_repository import BaseRepository
from core.repository.pk_strategy import PrimaryKeyValue
from core.type.common import JSONDict
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from sqlalchemy import func as sa_func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from llm.vector.fusion import FusionStrategy, HybridSearchConfig
from llm.vector.retrievers import RetrievalMode, RetrieverConfig
from llm.vector.store import VectorStore

_COUNT_EXPR = sa_func


def _count_expression() -> ColumnElement[int]:
    return _COUNT_EXPR.count()


class BaseVectorService[ModelT: Base](ABC):
    """一个抽象服务基类，封装了与向量存储进行同步的通用逻辑。

    子类需要实现 `_create_document_from_model` 方法来定义
    如何将特定的数据模型转换为用于向量化的 Document 对象。
    """

    def __init__(
        self,
        repository: BaseRepository[ModelT],
        table_name: str,
        collection_key: VectorCollectionKey,
        vector_store: VectorStore,
    ) -> None:
        """初始化基础向量服务（依赖注入）。

        Args:
            repository: 与服务关联的数据仓库实例。
            table_name: 业务数据主表名 (来自 `__tablename__`)。
            collection_key: 用于在 `config.yaml` 中查找配置的键 (例如, 'entities')。
            vector_store: 向量存储服务实例（注入）
        """
        self.repository = repository
        self.collection_name = f"{table_name}_embedding"
        self.collection_key = collection_key
        self._vector_store = vector_store

    @property
    def vector_store(self) -> VectorStore:
        """返回注入的 VectorStore 实例。"""
        return self._vector_store

    async def get_data_statistics(self, session: AsyncSession, group_by_field: str = "category") -> JSONDict:
        """获取数据的统计信息，包括总数和按指定字段分组的计数。

        Args:
            session: 数据库会话
            group_by_field: 分组字段名称
        """
        total_count = await self.repository.count_by(session)
        group_counts = await self._count_by_group(session, group_by_field)

        total_key = f"total_{self.collection_name.lower()}s"
        counts_key = f"{group_by_field}_counts"

        result: JSONDict = cast(
            JSONDict,
            {
                total_key: total_count,
                counts_key: group_counts,
            },
        )
        return result

    async def _count_by_group(self, session: AsyncSession, group_by_field: str) -> dict[str, int]:
        """直接在服务层进行分组聚合统计，避免 repository 暴露过多方法。"""
        model = self.repository.model
        if not hasattr(model, group_by_field):
            return {}
        group_column = getattr(model, group_by_field)
        stmt = select(group_column, _count_expression()).group_by(group_column)
        rows = await session.execute(stmt)
        return {str(row[0]): int(row[1]) for row in rows}

    @abstractmethod
    def create_document_from_model(self, model: ModelT) -> Document:
        """将数据模型实例转换为向量存储的 Document 对象。

        这是子类必须实现的抽象方法。
        """
        raise NotImplementedError

    async def _sync_upsert(self, _session: AsyncSession, models: list[ModelT]) -> None:
        """将一组数据模型同步（插入或更新）到向量存储。

        Args:
            _session: 数据库会话（基类不使用，子类可能需要）
            models: 需要向量化的模型列表
        """
        if not models:
            return
        docs = [self.create_document_from_model(model) for model in models]
        vector_size = core_config.llm_vectors.dimensions
        await self.vector_store.add_documents(self.collection_name, docs, vector_size)

    async def delete_vectors(self, vector_ids: list[str]) -> None:
        """从向量存储中删除一组文档。"""
        if not vector_ids:
            return
        vector_size = core_config.llm_vectors.dimensions
        await self.vector_store.delete_documents(self.collection_name, vector_ids, vector_size)

    def get_retriever(
        self,
        mode: RetrievalMode | str | None = None,
        k: int | None = None,
        filters: JSONDict | None = None,
        score_threshold: float | None = None,
    ) -> BaseRetriever:
        """获取配置好的LangChain Retriever实例。

        此方法提供标准的LangChain检索器接口，支持多种检索模式。
        优先级：方法参数 > collection配置 > 全局配置

        Args:
            mode: 检索模式（vector_only/fts_only/hybrid），None则使用配置
            k: 返回文档数量，None则使用配置
            filters: 元数据过滤条件
            score_threshold: 最低相关性分数，None则使用配置

        Returns:
            配置好的BaseRetriever实例（可直接调用ainvoke(query)）
        """
        collection_config = core_config.get_vector_collection_config(self.collection_key)

        if mode is None:
            try:
                final_mode = RetrievalMode(collection_config.search_type)
            except ValueError as e:
                valid_modes = [m.value for m in RetrievalMode]
                msg = f"配置中的search_type无效: '{collection_config.search_type}'。有效值: {valid_modes}"
                raise ValueError(msg) from e
        elif isinstance(mode, str):
            try:
                final_mode = RetrievalMode(mode)
            except ValueError as e:
                valid_modes = [m.value for m in RetrievalMode]
                msg = f"无效的检索模式: '{mode}'。有效值: {valid_modes}"
                raise ValueError(msg) from e
        else:
            final_mode = mode

        final_k = k if k is not None else collection_config.k
        final_score_threshold = score_threshold if score_threshold is not None else collection_config.score_threshold
        vector_size = core_config.llm_vectors.dimensions

        vector_weight = collection_config.alpha
        fts_weight = 1.0 - collection_config.alpha
        weights = [vector_weight, fts_weight]

        hybrid_config = HybridSearchConfig(
            strategy=FusionStrategy.RRF,
            vector_weight=vector_weight,
            fts_weight=fts_weight,
            rrf_k=collection_config.rrf_k,
            fetch_top_k=final_k,
            is_distance_metric=False,
        )
        retriever_config = RetrieverConfig(
            vector_store=self.vector_store,
            collection_name=self.collection_name,
            vector_size=vector_size,
            k=final_k,
            filters=cast(dict[str, Any] | None, filters),
            score_threshold=final_score_threshold,
            weights=weights,
            rrf_k=collection_config.rrf_k,
            hybrid_config=hybrid_config,
            rerank_score_threshold=collection_config.rerank_score_threshold,
            rerank_top_n=collection_config.rerank_top_n,
        )
        return self.vector_store.create_retriever(mode=final_mode, config=retriever_config)

    async def get_documents_by_ids(self, session: AsyncSession, ids: Sequence[str]) -> list[Document]:
        """根据ID列表从主数据源批量获取文档，并保证返回顺序与输入一致。

        Args:
            session: 数据库会话，需显式传入的 AsyncSession 实例。
            ids: 需要获取的文档ID列表。

        Returns:
            一个与输入ID顺序对应的Document对象列表。
        """
        if not ids:
            return []

        pk_values: list[PrimaryKeyValue] = [cast(PrimaryKeyValue, doc_id) for doc_id in ids]
        models: list[ModelT] = await self.repository.get_by_ids(session, pk_values)

        model_map: dict[Any, ModelT] = {}
        for model in models:
            if (model_id := cast(Any, getattr(model, "id", None))) is None:
                continue
            model_map[model_id] = model

        documents: list[Document] = []
        for doc_id in ids:
            if doc_id in model_map:
                model_instance = model_map[doc_id]
                doc = self.create_document_from_model(model_instance)
                documents.append(doc)

        return documents
