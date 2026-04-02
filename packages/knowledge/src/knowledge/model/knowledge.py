"""知识库文档领域模型"""

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Literal

from core.database import Base
from core.type import DescribableSchema, SchemaType
from pydantic import BaseModel, ConfigDict
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.elements import ColumnElement

if TYPE_CHECKING:
    from knowledge.model.section import KnowledgeSection


class KnowledgeStatus(StrEnum):
    """知识状态枚举"""

    PENDING = "pending"  # 文件已存 MinIO，等待 Worker 处理
    PROCESSING = "processing"  # Worker 已领取，正在处理
    ACTIVE = "active"  # 入库完成，正常可用
    FAILED = "failed"  # 处理失败，可重试或删除
    INACTIVE = "inactive"  # admin 手动停用


def _current_timestamp_expr() -> ColumnElement[datetime]:
    """提供统一的数据库时间表达式，避免 pylint not-callable 误报。"""
    return func.now()


class Knowledge(Base):
    """知识库文档模型，作为知识的逻辑容器。
    它存储知识的元数据，但不包含实际的文本内容，文本内容被分割存储在 KnowledgeChunk 中。

    RBAC 权限通过 Casbin 策略统一管理。
    """

    __tablename__ = "bedrock_knowledge"
    __table_args__ = ({"comment": "知识库文档表"},)
    id: Mapped[str] = mapped_column(String(255), primary_key=True, index=True, comment="知识ID")
    filename: Mapped[str] = mapped_column(String(255), nullable=False, index=True, comment="原始文件名")
    source: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="文档来源，如'文件上传'或特定URL",
    )

    # 所属知识库（必填）
    knowledge_base_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("bedrock_knowledge_base.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属知识库ID",
    )

    tags: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True, comment="文档标签列表，用于细粒度过滤")
    department: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True, comment="所属部门")
    language: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True, comment="知识语言代码(zh/en等)")
    folder_id: Mapped[str | None] = mapped_column(
        String(255),
        ForeignKey("bedrock_knowledge_folder.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="所属文件夹ID",
    )
    created_by: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="创建用户（来自 x-username header）",
    )
    owner_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="文档所有者")

    # 版本控制
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1", comment="文档版本号，从1开始递增")
    parent_id: Mapped[str | None] = mapped_column(
        String(255),
        ForeignKey("bedrock_knowledge.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="父知识ID，指向被更新的原文档",
    )
    is_latest: Mapped[bool] = mapped_column(nullable=False, server_default="true", index=True, comment="是否为最新版本")
    version_notes: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="版本更新说明")

    # 文件存储
    content_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="文件MIME类型，如'application/pdf'、'video/mp4'",
    )
    file_storage_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        index=True,
        comment="文件在存储系统中的路径",
    )
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="文件大小（字节）")
    knowledge_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="知识的其他元数据，如作者等",
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True, comment="AI 生成的文档摘要")

    # 状态管理
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="pending",
        index=True,
        comment="知识状态：pending/processing/active/failed/inactive",
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True, comment="入库失败错误信息")
    status_changed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="状态变更时间")
    status_changed_by: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="状态变更操作者")

    # 有效时间（用于定时生效/失效）
    valid_from: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        index=True,
        comment="生效开始时间，NULL表示立即生效",
    )
    valid_until: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        index=True,
        comment="失效时间，NULL表示永久有效",
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

    # 关联关系（懒加载，需要时使用 selectinload 预加载）
    sections: Mapped[list["KnowledgeSection"]] = relationship(
        "KnowledgeSection",
        back_populates="knowledge",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="KnowledgeSection.level, KnowledgeSection.order",
    )

    def __repr__(self) -> str:
        return f"<Knowledge(id='{self.id}', filename='{self.filename}', source='{self.source}')>"

    def get_storage_paths(self) -> list[str]:
        """获取所有需要清理的存储路径

        包括：
        - file_storage_path: 原始上传文件
        - office_pdf_path: 预览 PDF
        - thumbnail_path: 缩略图

        """
        paths: list[str] = []

        if self.file_storage_path:
            paths.append(self.file_storage_path)

        metadata: dict[str, Any] = self.knowledge_metadata or {}
        preview_meta = metadata.get("preview")
        if isinstance(preview_meta, dict):
            pdf_path = preview_meta.get("office_pdf_path")
            if isinstance(pdf_path, str) and pdf_path:
                paths.append(pdf_path)

            thumbnail_path = preview_meta.get("thumbnail_path")
            if isinstance(thumbnail_path, str) and thumbnail_path:
                paths.append(thumbnail_path)

        return paths


class KnowledgeSchema(DescribableSchema):
    schema_type: Literal[SchemaType.KNOWLEDGE_DOCUMENT] = SchemaType.KNOWLEDGE_DOCUMENT
    model_config = ConfigDict(from_attributes=True)
    id: str
    filename: str
    source: str
    knowledge_base_id: str
    tags: list[str] | None = None
    department: str | None = None
    language: str | None = None
    folder_id: str | None = None
    created_by: str
    owner_id: str
    version: int = 1
    parent_id: str | None = None
    is_latest: bool = True
    version_notes: str | None = None
    content_type: str | None = None
    file_storage_path: str | None = None
    file_size: int | None = None
    knowledge_metadata: dict[str, Any] | None = None
    summary: str | None = None
    status: str = KnowledgeStatus.PENDING
    error_message: str | None = None
    status_changed_at: datetime | None = None
    status_changed_by: str | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def name(self) -> str:
        return self.filename

    @property
    def description(self) -> str:
        parts = [f"来源: {self.source}"]
        if self.department:
            parts.append(f"部门: {self.department}")
        return "; ".join(parts)

    def to_llm_description_string(self) -> str:
        """返回一个为LLM选择优化的、包含丰富上下文的描述字符串。"""
        parts = [f"文件名: {self.filename}", f"来源: {self.source}"]
        if self.tags:
            parts.append(f"标签: {', '.join(self.tags)}")
        if self.department:
            parts.append(f"部门: {self.department}")
        return "; ".join(parts)


class KnowledgeCreateRequest(BaseModel):
    """创建知识的请求模型（用于CRUDRouterFactory）"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "产品需求文档",
                "description": "2024年Q1产品规划",
                "tags": ["需求", "规划"],
                "department": "产品部",
            },
        },
    )
    name: str
    description: str | None = None
    tags: list[str] | None = None
    department: str | None = None
    folder_id: str | None = None
    knowledge_metadata: dict[str, Any] | None = None


class KnowledgeUpdateRequest(BaseModel):
    """更新知识的请求模型，所有字段均为可选"""

    model_config = ConfigDict(from_attributes=True)
    name: str | None = None
    filename: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    department: str | None = None
    language: str | None = None
    folder_id: str | None = None
    knowledge_metadata: dict[str, Any] | None = None
    summary: str | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None


class KnowledgeCloneRequest(BaseModel):
    """克隆知识的请求模型（用于CRUDRouterFactory）"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "new_name": "产品需求文档-副本",
                "clone_content": True,
                "clone_permissions": False,
            },
        },
    )
    new_name: str
    clone_content: bool = True
    clone_permissions: bool = False
    tags: list[str] | None = None
    department: str | None = None
