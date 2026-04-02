"""知识库章节 Section 仓储"""

from typing import cast

from core.repository.base_repository import BaseRepository
from sqlalchemy import delete, select
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from knowledge.model.section import KnowledgeSection, SectionTreeNode


class KnowledgeSectionRepository(BaseRepository[KnowledgeSection]):
    """知识库章节仓储"""

    def __init__(self) -> None:
        super().__init__(KnowledgeSection)

    async def find_by_knowledge_id(
        self,
        session: AsyncSession,
        knowledge_id: str,
    ) -> list[KnowledgeSection]:
        """根据知识ID查找所有章节，按 level 和 order 排序。"""
        statement = (
            select(self.model)
            .where(self.model.knowledge_id == knowledge_id)
            .order_by(self.model.level, self.model.order)
        )
        result = await session.execute(statement)
        return list(result.scalars().all())

    async def find_by_knowledge_id_as_tree(
        self,
        session: AsyncSession,
        knowledge_id: str,
    ) -> list[SectionTreeNode]:
        """根据知识ID查找所有章节，返回树形结构。"""
        sections = await self.find_by_knowledge_id(session, knowledge_id)
        return self._build_tree(sections)

    async def find_by_ids(
        self,
        session: AsyncSession,
        section_ids: list[str],
    ) -> list[KnowledgeSection]:
        """根据章节ID列表批量查询。"""
        if not section_ids:
            return []
        statement = select(self.model).where(self.model.id.in_(section_ids))
        result = await session.execute(statement)
        return list(result.scalars().all())

    async def delete_by_knowledge_id(
        self,
        session: AsyncSession,
        knowledge_id: str,
    ) -> int:
        """删除指定知识的所有章节，返回删除数。"""
        statement = delete(self.model).where(self.model.knowledge_id == knowledge_id)
        result = cast("CursorResult[tuple[()]]", await session.execute(statement))
        return result.rowcount or 0

    async def bulk_create(
        self,
        session: AsyncSession,
        sections: list[KnowledgeSection],
    ) -> list[KnowledgeSection]:
        """批量创建章节。"""
        session.add_all(sections)
        await session.flush()
        return sections

    def _build_tree(self, sections: list[KnowledgeSection]) -> list[SectionTreeNode]:
        """将平铺的章节列表构建为树形结构。"""
        node_map: dict[str, SectionTreeNode] = {}
        for section in sections:
            node_map[section.id] = SectionTreeNode(
                id=section.id,
                title=section.title,
                level=section.level,
                order=section.order,
                start_page=section.start_page,
                anchor=section.anchor,
                section_type=section.section_type,
                children=[],
            )

        root_nodes: list[SectionTreeNode] = []
        for section in sections:
            node = node_map[section.id]
            if section.parent_section_id and section.parent_section_id in node_map:
                parent_node = node_map[section.parent_section_id]
                parent_node.children.append(node)
            else:
                root_nodes.append(node)

        return root_nodes
