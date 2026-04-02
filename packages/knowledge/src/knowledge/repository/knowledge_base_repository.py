"""KnowledgeBase Repository - 知识库顶层容器数据访问层"""

from core.logging import get_logger
from core.repository.base_repository import BaseRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from knowledge.model.knowledge_base import KnowledgeBase, KnowledgeBaseType
from core.type.permissions import is_admin

logger = get_logger(__name__)


class KnowledgeBaseRepository(BaseRepository[KnowledgeBase]):
    """知识库仓储，提供CRUD和权限查询功能"""

    def __init__(self) -> None:
        super().__init__(KnowledgeBase)

    async def find_accessible_bases(
        self,
        session: AsyncSession,
        user_id: str,
        is_admin: bool = False,
    ) -> list[KnowledgeBase]:
        """查询用户可访问的所有知识库（降级模式）

        注意：此方法仅用于降级场景（无 PermissionService 时）。
        正常情况下应使用 PermissionService 获取可访问 ID 后调用 find_by_ids。

        权限判断：
        - admin 角色：所有知识库
        - 普通用户：owner_id 匹配
        """
        if is_admin:
            # 管理员可以看到所有知识库
            stmt = select(self.model).order_by(self.model.created_at.desc())
        else:
            # 普通用户：仅查询 owner_id 匹配的记录
            stmt = select(self.model).where(self.model.owner_id == user_id).order_by(self.model.created_at.desc())

        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def find_by_ids(
        self,
        session: AsyncSession,
        ids: list[str],
        exclude_personal: bool = False,
    ) -> list[KnowledgeBase]:
        """根据 ID 列表查询知识库

        Args:
            session: 数据库会话
            ids: 知识库 ID 列表
            exclude_personal: 是否排除个人知识库

        Returns:
            知识库列表
        """
        if not ids:
            return []
        stmt = select(self.model).where(self.model.id.in_(ids))
        if exclude_personal:
            stmt = stmt.where(self.model.type != KnowledgeBaseType.PERSONAL)
        stmt = stmt.order_by(self.model.created_at.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def find_by_owner(
        self,
        session: AsyncSession,
        owner_id: str,
    ) -> list[KnowledgeBase]:
        """查询用户拥有的所有知识库"""
        stmt = select(self.model).where(self.model.owner_id == owner_id).order_by(self.model.created_at.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def check_access(
        self,
        session: AsyncSession,
        base_id: str,
        user_id: str,
        user_roles: list[str],
    ) -> bool:
        """检查用户是否有访问知识库的权限（RBAC 模式）

        权限条件（满足任一）：
        - 用户是 owner
        - 用户拥有 admin 角色

        其他权限（角色授权）应通过 ResourceAccessChecker 或 PermissionService 检查。

        Args:
            session: 数据库会话
            base_id: 知识库ID
            user_id: 用户ID
            user_roles: 用户角色列表

        Returns:
            是否有访问权限

        """
        base = await self.get_by_id(session, base_id)
        if not base:
            return False

        # 1. 检查所有者
        if base.owner_id == user_id:
            return True

        # 2. 检查 admin 角色
        return is_admin(user_roles)
