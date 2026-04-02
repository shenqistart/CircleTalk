"""
通用 CRUD Service 基类

提供标准的 CRUD 操作抽象，减少 Service 层的重复代码。

设计原则：
1. 泛型支持：使用 Generic[ModelType, SchemaType, RepoType] 保证类型安全
2. 钩子方法：提供 _before_create, _after_create 等钩子供子类扩展
3. 事务管理：API 层使用 session.begin() 管理事务边界，Service 层不 commit
4. 分页支持：统一的分页参数和响应格式
5. 权限集成：可选的权限检查钩子

使用示例：
    class SkillService(BaseCRUDService[Skill, SkillSchema, SkillRepository]):
        def __init__(self, repository: SkillRepository):
            super().__init__(repository)

        async def _after_create(self, model: Skill, schema: SkillSchema) -> None:
            # 自定义创建后逻辑
            await self._sync_to_vector_store(model)
"""

from collections.abc import Sequence

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import Base
from core.logging import get_logger
from core.repository.base_repository import BaseRepository
from core.repository.pk_strategy import PrimaryKeyValue

# 字符串到任意对象的字典类型，用于更新数据和过滤条件
StrObjectDict = dict[str, object]

logger = get_logger(__name__)


class BaseCRUDService[ModelType: Base, SchemaType: BaseModel]:
    """
    通用 CRUD Service 基类

    提供标准的 CRUD 操作：
    - create: 创建资源
    - get_by_id: 根据 ID 获取资源
    - get_by_ids: 批量获取资源
    - update: 更新资源
    - delete: 删除资源
    - search_paged: 分页查询

    钩子方法（供子类重写）：
    - _before_create: 创建前验证/转换
    - _after_create: 创建后处理（如同步到向量库）
    - _before_update: 更新前验证
    - _after_update: 更新后处理
    - _before_delete: 删除前验证
    - _after_delete: 删除后处理
    """

    def __init__(
        self,
        repository: BaseRepository[ModelType],
    ) -> None:
        """
        初始化 CRUD Service

        Args:
            repository: 数据仓储实例
        """
        self.repository: BaseRepository[ModelType] = repository
        logger.debug("初始化 %s", self.__class__.__name__)

    # ==================== 钩子方法（可选重写） ====================

    async def _before_create(self, schema: SchemaType) -> SchemaType:
        """
        创建前钩子：验证或转换输入数据

        Args:
            schema: 创建请求的 Schema

        Returns:
            处理后的 Schema（可修改字段）

        Raises:
            ValueError: 验证失败时抛出
        """
        return schema

    async def _after_create(self, session: AsyncSession, model: ModelType, schema: SchemaType) -> None:
        """
        创建后钩子：执行副作用（如同步到向量库、发送通知）

        Args:
            session: 当前数据库会话
            model: 创建的数据库模型
            schema: 创建请求的 Schema
        """

    async def _before_update(self, _model: ModelType, update_data: StrObjectDict) -> StrObjectDict:
        """
        更新前钩子：验证或转换更新数据

        Args:
            _model: 现有的数据库模型
            update_data: 更新字段字典

        Returns:
            处理后的更新字典

        Raises:
            ValueError: 验证失败时抛出
        """
        return update_data

    async def _after_update(self, session: AsyncSession, model: ModelType, update_data: StrObjectDict) -> None:
        """
        更新后钩子：执行副作用

        Args:
            session: 当前数据库会话
            model: 更新后的数据库模型
            update_data: 更新的字段字典
        """

    async def _before_delete(self, model: ModelType) -> None:
        """
        删除前钩子：验证或执行清理

        Args:
            model: 将要删除的数据库模型

        Raises:
            ValueError: 验证失败时抛出
        """

    async def _after_delete(self, session: AsyncSession, model_id: str) -> None:
        """
        删除后钩子：执行清理（如删除向量库数据）

        Args:
            session: 当前数据库会话
            model_id: 已删除的资源 ID
        """

    async def _build_filters(self, **kwargs: object) -> StrObjectDict:
        """
        构建查询过滤条件（供子类重写）

        Args:
            **kwargs: 查询参数

        Returns:
            过滤条件字典（传递给 Repository）
        """
        # 默认实现：过滤掉 None 值和分页参数
        filters: StrObjectDict = {}
        exclude_keys = {"page", "size", "limit", "offset"}
        for key, value in kwargs.items():
            if value is not None and key not in exclude_keys:
                filters[key] = value
        return filters

    # ==================== 核心 CRUD 方法 ====================

    async def create(
        self,
        session: AsyncSession,
        schema: SchemaType,
        **extra_fields: object,
    ) -> ModelType:
        """
        创建资源

        事务由 API 层通过 session.begin() 管理，Service 层不 commit。

        Args:
            session: 数据库会话
            schema: 创建请求的 Schema
            **extra_fields: 额外字段（如 created_by）

        Returns:
            创建的数据库模型

        Raises:
            ValueError: 验证失败
        """
        # 1. 前置钩子
        schema = await self._before_create(schema)

        # 2. 合并额外字段，构造新的 Schema
        if extra_fields:
            schema = schema.model_copy(update=dict(extra_fields))

        # 3. 调用 Repository 创建（显式传入 session）
        model = await self.repository.create(session, schema)

        # 4. 后置钩子
        await self._after_create(session, model, schema)

        logger.info("资源创建成功: %s id=%s", self.__class__.__name__, getattr(model, "id", "N/A"))
        return model

    async def get_by_id(
        self,
        session: AsyncSession,
        resource_id: str,
    ) -> ModelType | None:
        """
        根据 ID 获取资源

        Args:
            session: 数据库会话
            resource_id: 资源 ID

        Returns:
            数据库模型，如果不存在则返回 None
        """
        return await self.repository.get_by_id(session, resource_id)

    async def get_by_ids(
        self,
        session: AsyncSession,
        resource_ids: Sequence[PrimaryKeyValue],
    ) -> list[ModelType]:
        """
        批量获取资源

        Args:
            session: 数据库会话
            resource_ids: 资源 ID 列表

        Returns:
            数据库模型列表
        """
        return await self.repository.get_by_ids(session, list(resource_ids))

    async def update(
        self,
        session: AsyncSession,
        resource_id: str,
        update_data: StrObjectDict,
    ) -> ModelType | None:
        """
        更新资源

        事务由 API 层通过 session.begin() 管理，Service 层不 commit。

        Args:
            session: 数据库会话
            resource_id: 资源 ID
            update_data: 更新字段字典

        Returns:
            更新后的数据库模型，如果不存在则返回 None

        Raises:
            ValueError: 验证失败
        """
        # 1. 获取现有资源
        if not (model := await self.repository.get_by_id(session, resource_id)):
            return None

        # 2. 前置钩子
        update_data = await self._before_update(model, update_data)

        # 3. 调用 Repository 更新
        if updated_model := await self.repository.update(session, resource_id, update_data):
            await self._after_update(session, updated_model, update_data)

        logger.info("资源更新成功: %s id=%s", self.__class__.__name__, resource_id)
        return updated_model

    async def delete(
        self,
        session: AsyncSession,
        resource_id: str,
    ) -> bool:
        """
        删除资源

        事务由 API 层通过 session.begin() 管理，Service 层不 commit。

        Args:
            session: 数据库会话
            resource_id: 资源 ID

        Returns:
            True 如果删除成功，False 如果资源不存在

        Raises:
            ValueError: 验证失败
        """
        # 1. 获取现有资源
        if not (model := await self.repository.get_by_id(session, resource_id)):
            return False

        # 2. 前置钩子
        await self._before_delete(model)

        # 3. 调用 Repository 删除
        if success := await self.repository.delete(session, resource_id):
            await self._after_delete(session, resource_id)

        logger.info("资源删除成功: %s id=%s", self.__class__.__name__, resource_id)
        return success

    async def search_paged(
        self,
        session: AsyncSession,
        page: int = 1,
        size: int = 20,
        query: str | None = None,
        *,
        use_optimized: bool = True,
        **filters: object,
    ) -> tuple[list[ModelType], int]:
        """
        分页查询资源

        Args:
            session: 数据库会话
            page: 页码（从 1 开始）
            size: 每页数量
            query: 可选的搜索关键词
            use_optimized: 是否使用优化查询
            **filters: 过滤条件（传递给子类的 _build_filters）

        Returns:
            (数据列表, 总记录数) 元组
        """
        # 1. 构建过滤条件
        filter_dict = await self._build_filters(**filters)

        # 2. 查询分页数据
        results, total = await self.repository.search_paged(
            session,
            page,
            size=size,
            query=query,
            use_optimized=use_optimized,
            **filter_dict,
        )

        return results, total

    async def exists(
        self,
        session: AsyncSession,
        resource_id: str,
    ) -> bool:
        """
        检查资源是否存在

        Args:
            session: 数据库会话
            resource_id: 资源 ID

        Returns:
            True 如果存在，False 如果不存在
        """
        model = await self.repository.get_by_id(session, resource_id)
        return model is not None
