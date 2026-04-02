"""知识库分片领域模型"""

from datetime import datetime
from typing import Any, Literal

from core.database import Base
from core.model.fts_mixin import FTSMixin
from core.type import DescribableSchema, SchemaType
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.elements import ColumnElement

DESCRIPTION_PREVIEW_LENGTH = 150


def _current_timestamp_expr() -> ColumnElement[datetime]:
    """构造数据库当前时间表达式，避免 pylint 对 func.now() 误报。"""
    return func.now()


class KnowledgeChunk(Base, FTSMixin):
    """知识库分片模型，存储从文档中分割出的文本块。
    这是进行全文搜索和向量检索的基本单元。
    向量数据存储在专门的 embedding 表中。

    重构说明（2025-12）：
    - 移除 parent_chunk_id 和 chunk_type（Parent-Child 架构）
    - 新增 section_id 关联到 KnowledgeSection（结构感知分块）
    - 新增 start_char_index/end_char_index（支持动态上下文扩展）
    """

    __tablename__ = "bedrock_knowledge_chunk"
    __table_args__ = ({"comment": "知识库内容分片表"},)
    id: Mapped[str] = mapped_column(String(255), primary_key=True, index=True, comment="分片ID")
    knowledge_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("bedrock_knowledge.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属知识ID",
    )
    section_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        index=True,
        comment="所属章节ID（关联 KnowledgeSection）",
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="分片内容")
    chunk_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="分片的元数据，如页码、在文档中的起始位置等",
    )
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="分片在文档中的顺序")
    start_char_index: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="在文档中的起始字符位置（用于动态上下文扩展）",
    )
    end_char_index: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="在文档中的结束字符位置（用于动态上下文扩展）",
    )
    priority: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        index=True,
        comment="优先级：high/medium/low，用于检索时提升重要chunks的排序",
    )
    chunk_topics: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
        comment="chunk涉及的主题标签列表，用于精准过滤",
    )
    relevance_boost: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
        server_default="1.0",
        comment="检索时的相关性权重提升系数（默认1.0，重要chunks可设置>1.0）",
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=_current_timestamp_expr(),
        nullable=False,
        comment="记录创建时间",
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=_current_timestamp_expr(),
        onupdate=_current_timestamp_expr(),
        nullable=False,
        comment="记录更新时间",
    )

    def __repr__(self) -> str:
        return f"<KnowledgeChunk(id='{self.id}', knowledge_id='{self.knowledge_id}')>"

    def _get_fts_text(self) -> str:
        """为知识分片生成用于全文搜索的文本内容。"""
        return self.content


class KnowledgeChunkSchema(DescribableSchema):
    schema_type: Literal[SchemaType.KNOWLEDGE_CHUNK] = SchemaType.KNOWLEDGE_CHUNK
    model_config = ConfigDict(from_attributes=True)
    id: str
    knowledge_id: str
    section_id: str | None = None
    content: str
    chunk_metadata: dict[str, Any] | None = None
    order: int
    start_char_index: int | None = None
    end_char_index: int | None = None
    priority: str | None = Field(default=None, description="优先级：high/medium/low")
    chunk_topics: list[str] | None = Field(default=None, description="chunk涉及的主题标签")
    relevance_boost: float = Field(default=1.0, description="检索权重提升系数")
    created_at: datetime | None = Field(default=None, description="创建时间")
    updated_at: datetime | None = Field(default=None, description="更新时间")

    @property
    def description(self) -> str:
        if len(self.content) > DESCRIPTION_PREVIEW_LENGTH:
            return self.content[:DESCRIPTION_PREVIEW_LENGTH] + "..."
        return self.content

    def to_llm_description_string(self) -> str:
        """返回一个为LLM选择优化的、包含丰富上下文的描述字符串。"""
        return self.content


class KnowledgeChunkUpdate(BaseModel):
    """用于更新KnowledgeChunk的模型，所有字段均为可选。"""

    model_config = ConfigDict(from_attributes=True)
    content: str | None = None
    chunk_metadata: dict[str, Any] | None = None
    section_id: str | None = Field(default=None, description="所属章节ID")
    priority: str | None = Field(default=None, description="优先级：high/medium/low")
    chunk_topics: list[str] | None = Field(default=None, description="chunk涉及的主题标签")
    relevance_boost: float | None = Field(default=None, description="检索权重提升系数")
