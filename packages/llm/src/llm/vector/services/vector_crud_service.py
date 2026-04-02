"""向量增强的 CRUD Service 基类。

继承 BaseCRUDService 并集成向量同步功能，适用于需要向量检索的资源（如 Skill、Knowledge）。

设计原则：
1. 组合 BaseCRUDService 和 BaseVectorService 的功能
2. 自动在 CRUD 操作后同步向量库
3. 提供向量搜索能力
4. 事务由 API 层通过 session.begin() 管理，Service 层不 commit
"""

from enum import Enum
from typing import Any

from core.app_config import core_config
from core.database import Base, database_registry
from core.logging import get_logger
from core.repository.base_repository import BaseRepository
from core.service.base_crud_service import BaseCRUDService
from langchain_core.documents import Document
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from llm.vector.store import VectorStore

logger = get_logger(__name__)


class VectorCRUDService[ModelT: Base, SchemaT: BaseModel](BaseCRUDService[ModelT, SchemaT]):
    """向量增强的 CRUD Service 基类。

    在 BaseCRUDService 基础上添加：
    - 自动向量同步（创建/更新/删除后）
    - 向量检索能力（语义搜索）
    - Document 转换（模型 -> LangChain Document）
    """

    def __init__(
        self,
        repository: BaseRepository[ModelT],
        collection_name: str | Enum,
    ) -> None:
        """初始化向量增强的 CRUD Service。

        Args:
            repository: 数据仓储实例
            collection_name: 向量集合名称
        """
        super().__init__(repository)
        normalized_collection = collection_name.value if isinstance(collection_name, Enum) else str(collection_name)
        if not normalized_collection:
            msg = "collection_name 不能为空"
            raise ValueError(msg)
        self.collection_name = normalized_collection
        self.vector_store = VectorStore(registry=database_registry)
        self.vector_size = core_config.llm_vectors.dimensions
        logger.debug("初始化 %s，向量集合: %s", self.__class__.__name__, self.collection_name)

    async def _after_create(self, session: AsyncSession, model: ModelT, schema: SchemaT) -> None:
        """创建后自动同步到向量库。"""
        logger.debug(
            "准备同步创建的资源到向量库: %s，payload键: %s",
            getattr(model, "id", "N/A"),
            list(schema.model_dump().keys()),
        )
        await self._sync_upsert(session, [model])
        logger.debug("已同步创建的资源到向量库: %s", getattr(model, "id", "N/A"))

    async def _after_update(self, session: AsyncSession, model: ModelT, update_data: dict[str, Any]) -> None:
        """更新后自动重新同步到向量库。"""
        logger.debug(
            "准备同步更新的资源到向量库: %s，更新字段: %s",
            getattr(model, "id", "N/A"),
            list(update_data.keys()),
        )
        await self._sync_upsert(session, [model])
        logger.debug("已重新同步更新的资源到向量库: %s", getattr(model, "id", "N/A"))

    async def _after_delete(self, session: AsyncSession, model_id: str) -> None:
        """删除后自动清理向量库。"""
        _ = session  # 接口规范要求的参数
        await self.delete_vectors([model_id])
        logger.debug("已从向量库删除资源: %s", model_id)

    async def _sync_upsert(self, session: AsyncSession, models: list[ModelT]) -> None:
        """将模型同步（插入或更新）到向量存储。

        Args:
            session: 数据库会话（对齐接口，当前实现不使用）
            models: 要同步的模型列表
        """
        _ = session  # 接口规范要求的参数
        if not models:
            return

        documents = [self.create_document_from_model(model) for model in models]
        await self.vector_store.add_documents(
            collection=self.collection_name,
            documents=documents,
            vector_size=self.vector_size,
        )
        logger.info("成功同步 %s 个文档到向量库 '%s'", len(documents), self.collection_name)

    async def delete_vectors(self, model_ids: list[str]) -> None:
        """从向量存储中删除模型。

        Args:
            model_ids: 要删除的模型 ID 列表
        """
        if not model_ids:
            return

        await self.vector_store.delete_documents(
            collection=self.collection_name,
            document_ids=model_ids,
            vector_size=self.vector_size,
        )
        logger.info("成功从向量库 '%s' 删除 %s 个文档", self.collection_name, len(model_ids))

    async def search(
        self,
        session: AsyncSession | None,
        query: str,
        query_filter: dict[str, Any] | None = None,
        retrieval_limit: int | None = None,
        score_threshold: float | None = None,
    ) -> list[Document]:
        """基于向量相似度搜索资源。

        Args:
            session: 数据库会话，占位用于统一接口
            query: 搜索查询文本
            query_filter: 元数据过滤条件
            retrieval_limit: 返回结果数量限制
            score_threshold: 最低相似度分数阈值

        Returns:
            匹配的 LangChain Document 列表
        """
        if session is None:
            logger.debug("Vector search invoked without explicit session context; proceeding with vector store only.")

        k = retrieval_limit or 10
        threshold = score_threshold or 0.0

        results = await self.vector_store.similarity_search(
            collection_name=self.collection_name,
            query=query,
            k=k,
            filters=query_filter,
            score_threshold=threshold,
        )

        logger.info(
            "向量搜索完成: query='%s', collection='%s', results=%s, threshold=%s",
            query,
            self.collection_name,
            len(results),
            threshold,
        )
        return results

    async def get_all_documents(self, session: AsyncSession) -> list[Document]:
        """获取所有资源的 Document 表示。

        Returns:
            所有资源转换为 LangChain Document 列表
        """
        models = await self.repository.find_by(session)
        return [self.create_document_from_model(model) for model in models]

    async def upsert_batch(self, session: AsyncSession, schemas: list[SchemaT]) -> int:
        """批量 upsert 资源（插入或更新）。

        事务由 API 层通过 session.begin() 管理，Service 层不 commit。

        Args:
            schemas: 资源 Schema 列表
            session: 数据库会话，需显式传入的 AsyncSession 实例。

        Returns:
            成功 upsert 的数量
        """
        if not schemas:
            return 0

        if not hasattr(self.repository, "merge_batch"):
            msg = f"{self.repository.__class__.__name__} does not support merge_batch"
            raise RuntimeError(msg)

        if upserted_models := await self.repository.merge_batch(session, schemas):
            await self._sync_upsert(session, upserted_models)
        else:
            upserted_models = []

        logger.info("批量 upsert 完成: %s 个资源", len(upserted_models))
        return len(upserted_models)

    async def delete_batch(self, session: AsyncSession, model_ids: list[str]) -> int:
        """批量删除资源。

        事务由 API 层通过 session.begin() 管理，Service 层不 commit。

        Args:
            model_ids: 要删除的资源 ID 列表
            session: 数据库会话，需显式传入的 AsyncSession 实例。

        Returns:
            成功删除的数量
        """
        if not model_ids:
            return 0

        if not hasattr(self.repository, "delete_batch"):
            msg = f"{self.repository.__class__.__name__} does not support delete_batch"
            raise RuntimeError(msg)

        if (deleted_count := await self.repository.delete_batch(session, model_ids)) > 0:
            await self.delete_vectors(model_ids)

        logger.info("批量删除完成: %s 个资源", deleted_count)
        return deleted_count

    def create_document_from_model(self, model: ModelT) -> Document:
        """将模型转换为 LangChain Document（子类必须实现）。

        Args:
            model: SQLAlchemy 模型实例

        Returns:
            LangChain Document 对象
        """
        del model
        msg = f"{self.__class__.__name__} must implement create_document_from_model()"
        raise NotImplementedError(msg)
