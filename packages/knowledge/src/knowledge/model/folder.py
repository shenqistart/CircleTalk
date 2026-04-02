"""知识文件夹领域模型"""

from datetime import datetime
from typing import Any, Literal

from core.database import Base
from core.type import DescribableSchema, SchemaType
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.elements import ColumnElement


def _current_timestamp_expr() -> ColumnElement[datetime]:
    """统一 func.now() 调用，避免 pylint not-callable 误报。"""
    return func.now()


class KnowledgeFolder(Base):
    """知识库文件夹模型，支持无限层级的树形结构。
    通过 parent_folder_id 实现自引用，构建层级关系。

    RBAC 权限通过 Casbin 策略统一管理。
    """

    __tablename__ = "bedrock_knowledge_folder"
    __table_args__ = ({"comment": "知识文件夹表"},)
    id: Mapped[str] = mapped_column(String(255), primary_key=True, comment="文件夹ID")
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True, comment="文件夹名称")

    # 所属知识库（必填）
    knowledge_base_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("bedrock_knowledge_base.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属知识库ID",
    )

    parent_folder_id: Mapped[str | None] = mapped_column(
        String(255),
        ForeignKey("bedrock_knowledge_folder.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="父文件夹ID，null表示根文件夹",
    )
    owner_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="文件夹所有者")

    description: Mapped[str | None] = mapped_column(String(1000), nullable=True, comment="文件夹描述")
    folder_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True, comment="其他元数据")
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=_current_timestamp_expr(),
        nullable=False,
        comment="创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=_current_timestamp_expr(),
        onupdate=_current_timestamp_expr(),
        nullable=False,
        comment="更新时间",
    )

    def __repr__(self) -> str:
        return f"<KnowledgeFolder(id='{self.id}', name='{self.name}', knowledge_base='{self.knowledge_base_id}')>"


class KnowledgeFolderSchema(DescribableSchema):
    """知识库文件夹Schema"""

    model_config = ConfigDict(from_attributes=True)
    schema_type: Literal[SchemaType.KNOWLEDGE_FOLDER] = SchemaType.KNOWLEDGE_FOLDER
    id: str
    name: str
    knowledge_base_id: str
    parent_folder_id: str | None = None
    owner_id: str
    description: str | None = None
    folder_metadata: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    children: list["KnowledgeFolderSchema"] | None = None
    knowledge_count: int | None = None
    path: str | None = None

    def to_llm_description_string(self) -> str:
        """返回为 LLM 优化的描述字符串。"""
        parts = [f"文件夹名称: {self.name}"]
        if self.path:
            parts.append(f"路径: {self.path}")
        if self.description:
            parts.append(f"描述: {self.description}")
        if self.knowledge_count is not None:
            parts.append(f"包含知识: {self.knowledge_count}个")
        return "; ".join(parts)


class KnowledgeFolderCreate(BaseModel):
    """创建文件夹请求模型"""

    name: str = Field(..., min_length=1, max_length=255, description="文件夹名称")
    knowledge_base_id: str = Field(..., description="所属知识库ID（必填）")
    parent_folder_id: str | None = Field(None, description="父文件夹ID，null表示创建根文件夹")
    description: str | None = Field(None, max_length=1000, description="文件夹描述")
    folder_metadata: dict[str, Any] | None = Field(None, description="其他元数据")


class KnowledgeFolderUpdate(BaseModel):
    """更新文件夹请求模型"""

    model_config = ConfigDict(from_attributes=True)
    name: str | None = Field(None, min_length=1, max_length=255, description="文件夹名称")
    parent_folder_id: str | None = Field(None, description="父文件夹ID（移动文件夹）")
    description: str | None = Field(None, max_length=1000, description="文件夹描述")
    folder_metadata: dict[str, Any] | None = Field(None, description="其他元数据")
