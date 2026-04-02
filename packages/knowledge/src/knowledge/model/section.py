"""知识库章节/目录领域模型"""

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Literal

from core.database import Base
from core.type import DescribableSchema, SchemaType
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.elements import ColumnElement

if TYPE_CHECKING:
    from knowledge.model.knowledge import Knowledge


class SectionType(StrEnum):
    """章节类型枚举"""

    HEADING = "heading"  # 文档标题（Word/PDF heading）
    SLIDE = "slide"  # PPT 幻灯片
    SHEET = "sheet"  # Excel 工作表
    ROOT = "root"  # 根节点（整个文档 / 无结构时的回退）


def _current_timestamp_expr() -> ColumnElement[datetime]:
    """构造数据库当前时间表达式。"""
    return func.now()


class KnowledgeSection(Base):
    """知识库章节模型，存储文档的逻辑结构（目录/大纲）。
    用于：
    1. 前端展示文档目录树
    2. Chunk 归属定位（检索时显示来源章节）
    """

    __tablename__ = "bedrock_knowledge_section"
    __table_args__ = ({"comment": "知识库章节/目录表"},)

    id: Mapped[str] = mapped_column(String(255), primary_key=True, index=True, comment="章节ID")
    knowledge_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("bedrock_knowledge.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属知识ID",
    )

    # 树形结构
    parent_section_id: Mapped[str | None] = mapped_column(
        String(255),
        ForeignKey("bedrock_knowledge_section.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="父章节ID（NULL表示顶级章节）",
    )
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1, comment="层级深度：1=H1, 2=H2, 3=H3...")
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="同级章节排序")

    # 内容信息
    title: Mapped[str] = mapped_column(String(500), nullable=False, comment="章节标题")
    anchor: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="PDF bookmark / HTML anchor")

    # 定位信息
    start_page: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="起始页码（从1开始）")

    # 元数据
    section_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=SectionType.HEADING,
        server_default=SectionType.HEADING,
        index=True,
        comment="章节类型：heading/slide/sheet/root",
    )
    is_user_modified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="是否被用户修改过",
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=_current_timestamp_expr(),
        nullable=False,
        comment="记录创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=_current_timestamp_expr(),
        onupdate=_current_timestamp_expr(),
        nullable=False,
        comment="记录更新时间",
    )

    # 关联关系
    knowledge: Mapped["Knowledge"] = relationship("Knowledge", back_populates="sections")

    def __repr__(self) -> str:
        return f"<KnowledgeSection(id='{self.id}', title='{self.title}', level={self.level})>"


class KnowledgeSectionSchema(DescribableSchema):
    """章节数据传输 Schema"""

    schema_type: Literal[SchemaType.KNOWLEDGE_SECTION] = SchemaType.KNOWLEDGE_SECTION
    model_config = ConfigDict(from_attributes=True)

    id: str
    knowledge_id: str
    parent_section_id: str | None = None
    level: int = 1
    order: int = 0
    title: str
    anchor: str | None = None
    start_page: int | None = None
    section_type: str = SectionType.HEADING
    is_user_modified: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

    # 递归子节点（用于树形展示）
    children: list["KnowledgeSectionSchema"] = Field(default_factory=list)

    @property
    def name(self) -> str:
        return self.title

    @property
    def description(self) -> str:
        parts = [f"层级: {self.level}"]
        if self.start_page:
            parts.append(f"页码: {self.start_page}")
        return "; ".join(parts)

    def to_llm_description_string(self) -> str:
        """返回一个为 LLM 优化的描述字符串。"""
        return f"章节: {self.title}"


class KnowledgeSectionCreate(BaseModel):
    """创建章节请求模型"""

    model_config = ConfigDict(from_attributes=True)

    knowledge_id: str
    parent_section_id: str | None = None
    level: int = 1
    order: int = 0
    title: str
    anchor: str | None = None
    start_page: int | None = None
    section_type: str = SectionType.HEADING


class KnowledgeSectionUpdate(BaseModel):
    """更新章节请求模型（所有字段可选）"""

    model_config = ConfigDict(from_attributes=True)

    title: str | None = None
    anchor: str | None = None
    start_page: int | None = None
    is_user_modified: bool | None = None


class SectionTreeNode(BaseModel):
    """章节树节点（用于 API 返回）"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    level: int
    order: int
    start_page: int | None = None
    anchor: str | None = None
    section_type: str
    children: list["SectionTreeNode"] = Field(default_factory=list)
