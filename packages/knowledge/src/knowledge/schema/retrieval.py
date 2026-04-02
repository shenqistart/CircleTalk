"""知识检索相关 Schema 定义."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RetrievedChunk(BaseModel):
    """检索到的知识片段，工具返回的结构化表示."""

    model_config = ConfigDict(from_attributes=True)

    chunk_id: str | None = Field(default=None, description="Chunk ID（精确去重用）")
    snippet: str = Field(description="内容片段")
    source: str | None = Field(default=None, description="来源标识")
    page_no: str | None = Field(default=None, description="页码")
    knowledge_id: str | None = Field(default=None, description="知识 ID")
    score: float | None = Field(default=None, description="相关性分数")
    filename: str | None = Field(default=None, description="真实文件名")
    file_size: int | None = Field(default=None, description="文件大小")
    content_type: str | None = Field(default=None, description="MIME 类型")
    thumbnail_url: str | None = Field(default=None, description="缩略图 URL")
    preview_url: str | None = Field(default=None, description="预览 URL")
    chunk_topics: list[str] | None = Field(default=None, description="Chunk 主题标签")


class KnowledgeCitation(BaseModel):
    """知识引用信息（用于响应展示）."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="知识库条目 ID")
    title: str | None = Field(default=None, description="文档标题或名称")
    filename: str | None = Field(default=None, description="文件名")
    page_no: str | None = Field(default=None, description="页码")
    snippet: str | None = Field(default=None, description="内容片段")
    score: float | None = Field(default=None, description="相关性得分")
    file_size: int | None = Field(default=None, description="文件大小")
    content_type: str | None = Field(default=None, description="内容类型")
    thumbnail_url: str | None = Field(default=None, description="缩略图 URL")
    preview_url: str | None = Field(default=None, description="预览 URL")

    @classmethod
    def from_chunk(cls, chunk: RetrievedChunk) -> KnowledgeCitation:
        """从 RetrievedChunk 构建 Citation."""
        return cls(
            id=chunk.knowledge_id or "",
            filename=chunk.filename,
            page_no=chunk.page_no,
            snippet=chunk.snippet[:200] if chunk.snippet else None,
            score=chunk.score,
            file_size=chunk.file_size,
            content_type=chunk.content_type,
            thumbnail_url=chunk.thumbnail_url,
            preview_url=chunk.preview_url,
        )


__all__ = ["KnowledgeCitation", "RetrievedChunk"]
