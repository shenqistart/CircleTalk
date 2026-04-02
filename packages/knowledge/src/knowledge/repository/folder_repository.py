"""KnowledgeFolder Repository - 文件夹数据访问层"""

from core.logging import get_logger
from core.repository.base_repository import BaseRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import count

from knowledge.model.folder import KnowledgeFolder
from knowledge.model.knowledge import Knowledge

logger = get_logger(__name__)


class KnowledgeFolderRepository(BaseRepository[KnowledgeFolder]):
    """知识文件夹仓储，提供CRUD和树形查询功能"""

    def __init__(self) -> None:
        super().__init__(KnowledgeFolder)

    async def find_by_owner(
        self,
        session: AsyncSession,
        owner_id: str,
    ) -> list[KnowledgeFolder]:
        """查询用户拥有的所有文件夹"""
        stmt = select(self.model).where(self.model.owner_id == owner_id).order_by(self.model.created_at.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def find_root_folders(
        self,
        session: AsyncSession,
        owner_id: str | None = None,
        knowledge_base_id: str | None = None,
    ) -> list[KnowledgeFolder]:
        """查询根文件夹（parent_folder_id为null的文件夹）

        Args:
            owner_id: 可选的所有者过滤
            knowledge_base_id: 可选的知识库ID过滤
            session: 数据库会话

        """
        stmt = select(self.model).where(self.model.parent_folder_id.is_(None))
        if owner_id:
            stmt = stmt.where(self.model.owner_id == owner_id)
        if knowledge_base_id:
            stmt = stmt.where(self.model.knowledge_base_id == knowledge_base_id)
        stmt = stmt.order_by(self.model.name)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def find_by_knowledge_base(
        self,
        session: AsyncSession,
        knowledge_base_id: str,
    ) -> list[KnowledgeFolder]:
        """查询知识库下的所有文件夹"""
        stmt = (
            select(self.model)
            .where(self.model.knowledge_base_id == knowledge_base_id)
            .order_by(self.model.created_at.desc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def find_root_folders_in_base(
        self,
        session: AsyncSession,
        knowledge_base_id: str,
    ) -> list[KnowledgeFolder]:
        """查询知识库下的根文件夹（parent_folder_id为null）"""
        stmt = (
            select(self.model)
            .where(self.model.knowledge_base_id == knowledge_base_id)
            .where(self.model.parent_folder_id.is_(None))
            .order_by(self.model.name)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def find_children(
        self,
        session: AsyncSession,
        parent_id: str,
    ) -> list[KnowledgeFolder]:
        """查询指定文件夹的直接子文件夹"""
        stmt = select(self.model).where(self.model.parent_folder_id == parent_id).order_by(self.model.name)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_folder_path(
        self,
        session: AsyncSession,
        folder_id: str,
    ) -> str:
        """获取文件夹的完整路径（递归查询）
        返回格式：/一级文件夹/二级文件夹/当前文件夹
        """
        folder = await self.get_by_id(
            session,
            folder_id,
        )
        if not folder:
            return ""
        path_parts = [folder.name]
        current_folder = folder
        while current_folder.parent_folder_id:
            parent = await self.get_by_id(
                session,
                current_folder.parent_folder_id,
            )
            if not parent:
                break
            path_parts.insert(0, parent.name)
            current_folder = parent
        return "/" + "/".join(path_parts)

    @staticmethod
    async def count_knowledge_in_folder(
        session: AsyncSession,
        folder_id: str,
    ) -> int:
        """统计文件夹中的知识数量（不包括子文件夹）"""
        stmt = select(count(Knowledge.id)).where(Knowledge.folder_id == folder_id)
        result = await session.execute(stmt)
        return result.scalar_one()

    async def check_circular_reference(
        self,
        session: AsyncSession,
        folder_id: str,
        new_parent_id: str,
    ) -> bool:
        """检查是否会形成循环引用
        当移动文件夹时，需要确保新的父文件夹不是当前文件夹的子孙

        Returns:
            True: 会形成循环引用（不允许）
            False: 不会形成循环引用（允许）

        """
        if folder_id == new_parent_id:
            return True
        current_id = new_parent_id
        visited = set()
        while current_id:
            if current_id in visited:
                logger.warning("检测到数据库中的循环引用: %s", visited)
                return True
            if current_id == folder_id:
                return True
            visited.add(current_id)
            parent = await self.get_by_id(
                session,
                current_id,
            )
            if not parent:
                break
            current_id = parent.parent_folder_id
        return False

    async def count_knowledge_in_folder_recursive(
        self,
        session: AsyncSession,
        folder_id: str,
    ) -> int:
        """递归统计文件夹及其所有子文件夹中的知识数量

        Args:
            session: 数据库会话
            folder_id: 文件夹ID

        Returns:
            文件夹及其所有子文件夹的知识总数

        """
        # 统计当前文件夹的知识数量
        total = await self.count_knowledge_in_folder(session, folder_id)

        # 递归统计所有子文件夹
        children = await self.find_children(session, folder_id)
        for child in children:
            child_count = await self.count_knowledge_in_folder_recursive(session, child.id)
            total += child_count

        return total

    async def get_all_descendant_ids(
        self,
        session: AsyncSession,
        folder_id: str,
    ) -> list[str]:
        """递归获取所有子文件夹 ID（不包含当前文件夹）

        Args:
            session: 数据库会话
            folder_id: 文件夹ID

        Returns:
            所有子文件夹 ID 列表

        """
        descendant_ids: list[str] = []
        children = await self.find_children(session, folder_id)
        for child in children:
            descendant_ids.append(child.id)
            child_descendants = await self.get_all_descendant_ids(session, child.id)
            descendant_ids.extend(child_descendants)
        return descendant_ids
