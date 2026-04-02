"""知识（Knowledge）模型的数据库操作封装"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import cast

from core.logging import get_logger
from core.repository.base_repository import BaseRepository
from core.type.common import StrObjectDict
from sqlalchemy import String, Text, and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.functions import count

from knowledge.model.knowledge import Knowledge, KnowledgeStatus

logger = get_logger(__name__)


@dataclass(frozen=True)
class Pagination:
    """分页参数"""

    page: int
    size: int

    def offset(self) -> int:
        """转换为 SQL offset"""
        return (self.page - 1) * self.size


class KnowledgeRepository(BaseRepository[Knowledge]):
    """知识（Knowledge）的仓储实现"""

    def __init__(self) -> None:
        super().__init__(Knowledge)

    def _get_searchable_fields(self) -> list[str]:
        """返回 Knowledge 可搜索的字段。"""
        return ["filename", "source", "department"]

    def build_validity_filters(self, now: datetime | None = None) -> list[ColumnElement[bool]]:
        """构建有效性过滤条件（status=active 且在有效期内）。

        Args:
            now: 当前时间，默认使用 datetime.now()

        Returns:
            SQLAlchemy 过滤条件列表

        """
        if now is None:
            now = datetime.now()

        return [
            # 状态为 active
            Knowledge.status == KnowledgeStatus.ACTIVE,
            # valid_from 为空或已到达生效时间
            or_(Knowledge.valid_from.is_(None), Knowledge.valid_from <= now),
            # valid_until 为空或尚未过期
            or_(Knowledge.valid_until.is_(None), Knowledge.valid_until > now),
        ]

    def _build_search_clauses(self, query: str) -> list[ColumnElement[bool]]:
        """构造模糊搜索条件"""
        clauses: list[ColumnElement[bool]] = []
        for field_name in self._get_searchable_fields():
            if not hasattr(self.model, field_name):
                continue
            attr = getattr(self.model, field_name)
            if not hasattr(attr.property, "columns"):
                continue
            column = attr.property.columns[0]
            if isinstance(column.type, (String, Text)):
                clauses.append(attr.ilike(f"%{query}%"))
        if not clauses:
            return []
        return [or_(*clauses)]

    def _build_kwarg_filters(self, **filters: object) -> list[ColumnElement[bool]]:
        """从kwargs构建过滤条件。

        Args:
            **kwargs: 字段名=值的过滤参数

        Returns:
            过滤条件列表

        """
        clauses: list[ColumnElement[bool]] = []
        typed_filters = cast("StrObjectDict", filters)
        for key, value in typed_filters.items():
            if value is not None and hasattr(self.model, key):
                clauses.append(getattr(self.model, key) == value)
        return clauses

    async def _execute_paged_search(
        self,
        session: AsyncSession,
        pagination: Pagination,
        *,
        query: str | None = None,
        extra_filters: Sequence[ColumnElement[bool]] | None = None,
        **filters: object,
    ) -> tuple[list[Knowledge], int]:
        """执行分页搜索的通用逻辑。

        Args:
            pagination: 分页参数
            query: 搜索关键词（可选）
            extra_filters: 额外的过滤条件（如权限过滤）
            session: 数据库会话
            **kwargs: 其他字段过滤条件

        Returns:
            (文档列表, 总数)

        """
        stmt = select(self.model)
        where_clauses = list(extra_filters) if extra_filters else []
        if query:
            where_clauses.extend(self._build_search_clauses(query))
        where_clauses.extend(self._build_kwarg_filters(**filters))
        if where_clauses:
            stmt = stmt.where(and_(*where_clauses))
        total_query = select(count()).select_from(stmt.subquery())
        total_result = await session.execute(total_query)
        if (total := total_result.scalar_one()) == 0:
            return ([], 0)
        paged_query = stmt.order_by(self.model.created_at.desc()).offset(pagination.offset()).limit(pagination.size)
        result = await session.execute(paged_query)
        items = list(result.scalars().all())
        return (items, total)

    async def search_accessible_paged(
        self,
        session: AsyncSession,
        user_id: str,
        pagination: Pagination,
        query: str | None = None,
        **filters: object,
    ) -> tuple[list[Knowledge], int]:
        """文档专用的分页搜索方法（已废弃，将被新的权限系统替代）

        注意：此方法使用旧的权限模型，建议使用 Service 层的权限检查

        Args:
            session: 数据库会话
            user_id: 当前用户ID
            pagination: 分页参数
            query: 搜索关键词
            **kwargs: 其他过滤条件

        """
        # 暂时只按 owner_id 过滤，权限由 Service 层处理
        access_filter = self.model.owner_id == user_id
        return await self._execute_paged_search(
            session,
            pagination,
            query=query,
            extra_filters=[access_filter],
            **filters,
        )

    async def find_by_folder(
        self,
        session: AsyncSession,
        folder_id: str | None,
    ) -> list[Knowledge]:
        """根据文件夹ID查找文档

        Args:
            folder_id: 文件夹ID，None表示查询根目录（folder_id为null）的文档
            session: 数据库会话

        """
        if folder_id is None:
            stmt = select(self.model).where(self.model.folder_id.is_(None))
        else:
            stmt = select(self.model).where(self.model.folder_id == folder_id)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def find_by_knowledge_base(
        self,
        session: AsyncSession,
        knowledge_base_id: str,
    ) -> list[Knowledge]:
        """查询知识库下的所有文档"""
        stmt = (
            select(self.model)
            .where(self.model.knowledge_base_id == knowledge_base_id)
            .order_by(self.model.created_at.desc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def find_ids_by_base(
        self,
        session: AsyncSession,
        knowledge_base_id: str,
    ) -> list[str]:
        """查询知识库下所有文档的 ID 列表。

        用于技能资源绑定范围计算，只返回 ID 提高效率。

        Args:
            session: 数据库会话
            knowledge_base_id: 知识库ID

        Returns:
            知识 ID 列表

        """
        stmt = select(self.model.id).where(self.model.knowledge_base_id == knowledge_base_id)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def find_valid_ids(
        self,
        session: AsyncSession,
        knowledge_ids: list[str] | None = None,
        now: datetime | None = None,
    ) -> list[str]:
        """查询当前有效的知识 ID 列表。

        有效性判断：status=active 且在有效期内（valid_from <= now < valid_until）。

        Args:
            session: 数据库会话
            knowledge_ids: 限定范围的知识 ID 列表，为 None 时查询所有
            now: 当前时间，默认使用 datetime.now()

        Returns:
            有效的知识 ID 列表

        """
        validity_filters = self.build_validity_filters(now)
        stmt = select(self.model.id).where(and_(*validity_filters))

        if knowledge_ids is not None:
            stmt = stmt.where(self.model.id.in_(knowledge_ids))

        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def find_root_knowledge(
        self,
        session: AsyncSession,
        knowledge_base_id: str,
    ) -> list[Knowledge]:
        """查询知识库根目录的文档（不属于任何文件夹）。

        用于懒加载树形展示，仅返回 folder_id 为空且为最新版本的知识。

        Args:
            session: 数据库会话
            knowledge_base_id: 知识库ID

        Returns:
            根目录文档列表

        """
        stmt = (
            select(self.model)
            .where(self.model.knowledge_base_id == knowledge_base_id)
            .where(self.model.folder_id.is_(None))
            .where(self.model.is_latest.is_(True))
            .order_by(self.model.created_at.desc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def find_by_base_with_pagination(
        self,
        session: AsyncSession,
        knowledge_base_id: str,
        pagination: Pagination,
        *,
        folder_id: str | None = None,
        query: str | None = None,
        **filters: object,
    ) -> tuple[list[Knowledge], int]:
        """按知识库和文件夹查询文档（支持分页和搜索）

        Args:
            session: 数据库会话
            knowledge_base_id: 知识库ID
            pagination: 分页参数
            folder_id: 文件夹ID（可选，None表示不按文件夹过滤）
            query: 搜索关键词（可选）
            **filters: 其他过滤条件（department, tags等）

        Returns:
            (文档列表, 总数)

        """
        extra_filters = [self.model.knowledge_base_id == knowledge_base_id]
        if folder_id is not None:
            # 空字符串表示根目录（folder_id IS NULL）
            if folder_id == "":
                extra_filters.append(self.model.folder_id.is_(None))
            else:
                extra_filters.append(self.model.folder_id == folder_id)
        return await self._execute_paged_search(
            session,
            pagination,
            query=query,
            extra_filters=extra_filters,
            **filters,
        )

    async def find_by_tags(
        self,
        session: AsyncSession,
        tags: list[str],
    ) -> list[Knowledge]:
        """根据标签查找文档（包含任一标签即可）"""
        statement = select(self.model).where(self.model.tags.overlap(tags))
        result = await session.execute(statement)
        return list(result.scalars().all())

    async def find_by_department(
        self,
        session: AsyncSession,
        department: str,
    ) -> list[Knowledge]:
        """根据部门查找文档"""
        return await self.get_by_filters(
            session,
            {"department": department},
        )

    async def get_all_departments(self, session: AsyncSession) -> list[str]:
        """获取所有部门"""
        statement = select(self.model.department).where(self.model.department.isnot(None)).distinct()
        result = await session.execute(statement)
        return [dept for dept in result.scalars().all() if dept]

    async def get_all_tags(self, session: AsyncSession) -> list[str]:
        """获取所有使用过的标签"""
        statement = select(func.jsonb_array_elements_text(self.model.tags)).where(self.model.tags.isnot(None))
        result = await session.execute(statement)
        tags = list(set(result.scalars().all()))
        return sorted(tags)

    async def find_by_owner(
        self,
        session: AsyncSession,
        owner_id: str,
    ) -> list[Knowledge]:
        """查找指定用户拥有的所有文档（按创建时间倒序）"""
        statement = select(self.model).where(self.model.owner_id == owner_id).order_by(self.model.created_at.desc())
        result = await session.execute(statement)
        return list(result.scalars().all())

    async def find_accessible_documents(
        self,
        session: AsyncSession,
        user_id: str,
    ) -> list[Knowledge]:
        """查找用户有权访问的所有文档（已废弃）

        注意：此方法使用旧的权限模型，建议使用 Service 层的权限检查
        """
        # 暂时只返回用户拥有的文档
        statement = select(self.model).where(self.model.owner_id == user_id)
        result = await session.execute(statement)
        return list(result.scalars().all())

    async def _find_root_document(
        self,
        session: AsyncSession,
        knowledge_id: str,
    ) -> Knowledge | None:
        """查找版本链的根文档。
        如果传入的文档有parent_id，向上追溯直到找到根文档（parent_id为NULL）。

        Args:
            knowledge_id: 任意版本的知识ID
            session: 数据库会话

        Returns:
            根文档对象，如果不存在则返回None

        """
        current_doc = await self.get_by_id(
            session,
            knowledge_id,
        )
        if not current_doc:
            return None
        visited = set()
        while current_doc.parent_id:
            if current_doc.id in visited:
                logger.warning("检测到文档版本链循环引用: %s", visited)
                break
            visited.add(current_doc.id)
            parent_doc = await self.get_by_id(
                session,
                current_doc.parent_id,
            )
            if not parent_doc:
                break
            current_doc = parent_doc
        return current_doc

    async def get_version_history(
        self,
        session: AsyncSession,
        knowledge_id: str,
    ) -> list[Knowledge]:
        """获取知识的所有版本历史。
        返回指定文档及其所有版本，按版本号降序排列。

        算法：
        1. 找到根文档（向上遍历）
        2. 从根文档开始，递归收集所有子版本（向下遍历）
        """
        root_doc = await self._find_root_document(
            session,
            knowledge_id,
        )
        if not root_doc:
            return []
        versions = []

        async def collect_versions(knowledge_item: Knowledge) -> None:
            """递归收集知识的所有子版本"""
            versions.append(knowledge_item)
            stmt = select(self.model).where(self.model.parent_id == knowledge_item.id)
            result = await session.execute(stmt)
            children = list(result.scalars().all())
            for child in children:
                await collect_versions(child)

        await collect_versions(root_doc)
        versions.sort(key=lambda d: d.version, reverse=True)
        return versions

    async def get_latest_version(
        self,
        session: AsyncSession,
        knowledge_id: str,
    ) -> Knowledge | None:
        """获取知识的最新版本。
        如果传入的是旧版本，返回该版本链的最新版本。
        """
        versions = await self.get_version_history(
            session,
            knowledge_id,
        )
        if not versions:
            return None
        for version in versions:
            if version.is_latest:
                return version
        return max(versions, key=lambda d: d.version)
