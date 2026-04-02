"""Knowledge 模块配置

提供知识库处理相关的配置参数，避免硬编码。
"""

from pydantic import BaseModel, Field


class ChunkingConfig(BaseModel):
    """知识库分块配置"""

    parent_chunk_size: int = Field(default=1200, description="父块大小（字符数）")
    parent_chunk_overlap: int = Field(default=200, description="父块重叠大小")
    child_chunk_size: int = Field(default=800, description="子块大小（字符数），≈400 tokens")
    child_chunk_overlap: int = Field(default=120, description="子块重叠大小（15% overlap）")


class KnowledgeStorageConfig(BaseModel):
    """知识库存储配置"""

    presigned_url_expires: int = Field(default=900, description="预签名URL有效期（秒）")
    upload_max_size: int = Field(default=104857600, description="上传文件最大大小（字节），默认100MB")


class SummarizerConfig(BaseModel):
    """入库自动摘要/标签生成配置"""

    enabled: bool = Field(default=True, description="是否启用自动生成")
    max_content_length: int = Field(default=12000, description="送入 LLM 的最大文档字符数")


class KnowledgeConfig(BaseModel):
    """知识库模块总配置"""

    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig, description="分块配置")
    storage: KnowledgeStorageConfig = Field(default_factory=KnowledgeStorageConfig, description="存储配置")
    summarizer: SummarizerConfig = Field(default_factory=SummarizerConfig, description="自动摘要/标签配置")


knowledge_config = KnowledgeConfig()
