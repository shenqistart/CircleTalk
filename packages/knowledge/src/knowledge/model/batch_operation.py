"""批量操作数据模型

定义批量上传、批量删除、批量更新等操作的请求和响应模型，
以及知识元数据更新的选项对象。
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from knowledge.model.knowledge import KnowledgeSchema


class BatchUploadResult(BaseModel):
    """批量上传结果"""

    success_count: int = Field(..., description="成功上传的文件数量")
    failed_count: int = Field(..., description="上传失败的文件数量")
    succeeded: list[KnowledgeSchema] = Field(default_factory=list, description="成功上传的文档列表")
    failed: list[dict[str, Any]] = Field(default_factory=list, description="上传失败的文件列表 [{filename, error}]")


class StoreResult(BaseModel):
    """Phase 1 存储结果（仅文件上传 + 记录创建）"""

    knowledge_id: str = Field(..., description="知识 ID")
    filename: str = Field(..., description="文件名")
    status: str = Field(default="stored", description="状态")
    file_size: int = Field(..., description="文件大小（字节）")
    content_type: str = Field(..., description="文件 MIME 类型")


class BatchDeleteRequest(BaseModel):
    """批量删除请求"""

    knowledge_ids: list[str] = Field(..., description="要删除的知识ID列表", min_length=1, max_length=100)


class BatchDeleteResult(BaseModel):
    """批量删除结果"""

    success_count: int = Field(..., description="成功删除的文档数量")
    failed_count: int = Field(..., description="删除失败的文档数量")
    succeeded: list[str] = Field(default_factory=list, description="成功删除的知识ID列表")
    failed: list[dict[str, Any]] = Field(default_factory=list, description="删除失败的文档列表 [{knowledge_id, error}]")


class BatchExportRequest(BaseModel):
    """批量导出请求"""

    knowledge_ids: list[str] = Field(..., description="要导出的知识ID列表", min_length=1, max_length=50)


class BatchMetadataUpdateRequest(BaseModel):
    """批量元数据更新请求"""

    knowledge_ids: list[str] = Field(..., description="要更新的知识ID列表", min_length=1, max_length=100)
    category: str | None = Field(None, description="文档分类")
    tags: list[str] | None = Field(None, description="文档标签")
    department: str | None = Field(None, description="所属部门")


class BatchMetadataUpdateResult(BaseModel):
    """批量元数据更新结果"""

    success_count: int = Field(..., description="成功更新的文档数量")
    failed_count: int = Field(..., description="更新失败的文档数量")
    succeeded: list[str] = Field(default_factory=list, description="成功更新的知识ID列表")
    failed: list[dict[str, Any]] = Field(default_factory=list, description="更新失败的文档列表 [{knowledge_id, error}]")


@dataclass(slots=True)
class KnowledgeMetadataUpdateOptions:
    """封装知识元数据更新可选字段，避免函数参数过多。"""

    tags: list[str] | None = None
    department: str | None = None
    language: str | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
