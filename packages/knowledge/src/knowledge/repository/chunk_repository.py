"""知识分片 Chunk 仓储"""

from core.repository.base_repository import BaseRepository
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from knowledge.model.chunk import KnowledgeChunk


class KnowledgeChunkRepository(BaseRepository[KnowledgeChunk]):
    """知识分片 Chunk 仓储"""

    def __init__(self) -> None:
        super().__init__(KnowledgeChunk)

    async def find_by_knowledge_id(
        self,
        session: AsyncSession,
        knowledge_id: str,
    ) -> list[KnowledgeChunk]:
        """根据知识ID查找所有关联的分片，按 order 排序。"""
        statement = select(self.model).where(self.model.knowledge_id == knowledge_id).order_by(self.model.order)
        result = await session.execute(statement)
        return list(result.scalars().all())

    async def find_by_section_id(
        self,
        session: AsyncSession,
        section_id: str,
    ) -> list[KnowledgeChunk]:
        """根据章节ID查找所有关联的分片，按 order 排序。"""
        statement = select(self.model).where(self.model.section_id == section_id).order_by(self.model.order)
        result = await session.execute(statement)
        return list(result.scalars().all())

    async def find_by_priority(
        self,
        session: AsyncSession,
        priority: str,
        knowledge_id: str | None = None,
    ) -> list[KnowledgeChunk]:
        """根据优先级查询 chunks。"""
        statement = select(self.model).where(self.model.priority == priority)
        if knowledge_id:
            statement = statement.where(self.model.knowledge_id == knowledge_id)
        result = await session.execute(statement)
        return list(result.scalars().all())

    async def find_by_topics(
        self,
        session: AsyncSession,
        topics: list[str],
        knowledge_id: str | None = None,
    ) -> list[KnowledgeChunk]:
        """根据主题标签查询 chunks（匹配任一标签）。"""
        statement = select(self.model).where(
            func.array_length(self.model.chunk_topics, 1).isnot(None),
            self.model.chunk_topics.op("&&")(topics),
        )
        if knowledge_id:
            statement = statement.where(self.model.knowledge_id == knowledge_id)
        result = await session.execute(statement)
        return list(result.scalars().all())

    async def count_by_section_grouped(
        self,
        session: AsyncSession,
        knowledge_id: str,
    ) -> dict[str | None, int]:
        """按 section_id 分组统计 chunk 数量。

        Args:
            session: 数据库会话
            knowledge_id: 知识ID

        Returns:
            字典，key 为 section_id（None 表示未归类），value 为 chunk 数量

        """
        statement = (
            select(self.model.section_id, func.count(self.model.id))
            .where(self.model.knowledge_id == knowledge_id)
            .group_by(self.model.section_id)
        )
        result = await session.execute(statement)
        return {row[0]: row[1] for row in result.all()}
