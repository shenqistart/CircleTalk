"""知识库顶层容器领域模型"""

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from core.database import Base
from core.type import DescribableSchema, SchemaType
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import DateTime, String, func, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.elements import ColumnElement


class KnowledgeBaseType(StrEnum):
    """知识库类型枚举"""

    STANDARD = "standard"  # 标准知识库
    PERSONAL = "personal"  # 个人知识库


def _current_timestamp_expr() -> ColumnElement[datetime]:
    """统一 func.now() 调用，避免 pylint not-callable 误报。"""
    return func.now()


class KnowledgeBase(Base):
    """知识库顶层容器模型，实现三层架构的顶层。

    三层架构：
    - KnowledgeBase（知识库）: 项目/主题级的容器，如"产品文档库"、"技术文档库"
    - KnowledgeFolder（文件夹）: 树形组织结构
    - Knowledge（文档）: 具体的知识文档

    RBAC 权限通过 Casbin 策略统一管理。
    allowed_roles 保留用于兼容旧数据。
    """

    __tablename__ = "bedrock_knowledge_base"
    __table_args__ = ({"comment": "知识库顶层容器表"},)

    # 基础信息
    id: Mapped[str] = mapped_column(String(255), primary_key=True, index=True, comment="知识库ID")
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True, comment="知识库名称")
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True, comment="知识库描述")

    # 所有权
    owner_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="知识库所有者")

    # 知识库类型
    type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="standard",
        index=True,
        comment="知识库类型: standard/personal",
    )

    # RBAC 权限（旧版：角色白名单，保留用于兼容）
    allowed_roles: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        server_default=text("ARRAY[]::text[]"),
        comment="允许访问的角色列表（兼容旧数据）",
    )

    # 扩展元数据
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True, comment="扩展元数据")

    # 时间戳
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
        return f"<KnowledgeBase(id='{self.id}', name='{self.name}', owner='{self.owner_id}')>"


class KnowledgeBaseSchema(DescribableSchema):
    """知识库Schema"""

    model_config = ConfigDict(from_attributes=True)
    schema_type: Literal[SchemaType.KNOWLEDGE_BASE] = SchemaType.KNOWLEDGE_BASE
    id: str
    name: str
    description: str | None = None
    owner_id: str
    type: KnowledgeBaseType = KnowledgeBaseType.STANDARD
    allowed_roles: list[str] = Field(default_factory=list)
    extra_metadata: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    # 统计信息（可选，由 Service 层填充）
    folder_count: int | None = None
    document_count: int | None = None

    def to_llm_description_string(self) -> str:
        """返回为 LLM 优化的描述字符串。"""
        parts = [f"知识库名称: {self.name}"]
        if self.description:
            parts.append(f"描述: {self.description}")
        if self.folder_count is not None:
            parts.append(f"包含文件夹: {self.folder_count}个")
        if self.document_count is not None:
            parts.append(f"包含文档: {self.document_count}个")
        return "; ".join(parts)


class KnowledgeBaseCreate(BaseModel):
    """创建知识库请求模型"""

    id: str | None = Field(None, max_length=255, description="知识库ID（可选，不传则自动生成）")
    name: str = Field(..., min_length=1, max_length=255, description="知识库名称")
    description: str | None = Field(None, max_length=1000, description="知识库描述")
    type: KnowledgeBaseType = Field(default=KnowledgeBaseType.STANDARD, description="知识库类型")
    allowed_roles: list[str] = Field(default_factory=list, description="允许访问的角色列表（兼容旧数据）")
    extra_metadata: dict[str, Any] | None = Field(None, description="扩展元数据")


class KnowledgeBaseUpdate(BaseModel):
    """更新知识库请求模型"""

    model_config = ConfigDict(from_attributes=True)
    name: str | None = Field(default=None, min_length=1, max_length=255, description="知识库名称")
    description: str | None = Field(default=None, max_length=1000, description="知识库描述")
    owner_id: str | None = Field(default=None, max_length=100, description="知识库所有者")
    allowed_roles: list[str] | None = Field(default=None, description="允许访问的角色列表（兼容旧数据）")
    extra_metadata: dict[str, Any] | None = Field(default=None, description="扩展元数据")
