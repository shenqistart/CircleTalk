"""DashScope Embedding 客户端。

继承 BaseAsyncEmbeddings，实现 DashScope 特定的 API 调用逻辑。
支持两种 API 模式：
- Native API: /api/v1/services/embeddings/text-embedding/text-embedding
- OpenAI Compatible API: /compatible-mode/v1/embeddings
"""

from __future__ import annotations

from typing import cast

from core.logging import get_logger
from core.type.common import JSONDict
from core.utils.env import EnvUtils
from pydantic import BaseModel, model_validator

from llm.vector.embeddings.base import BaseAsyncEmbeddings

logger = get_logger(__name__)

# 默认端点常量（base_url 为 None 时回退到公网 Native API）
_DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/api/v1"


class _OpenAIEmbeddingItem(BaseModel):
    """OpenAI 兼容模式的单条 Embedding 数据。"""

    embedding: list[float]
    index: int


class _OpenAIEmbeddingResponse(BaseModel):
    """OpenAI 兼容模式的完整响应。"""

    data: list[_OpenAIEmbeddingItem]


class _NativeEmbeddingItem(BaseModel):
    """Native API 的单条 Embedding 数据。"""

    embedding: list[float]
    text_index: int


class _NativeEmbeddingOutput(BaseModel):
    """Native API 响应的 output 字段。"""

    embeddings: list[_NativeEmbeddingItem]


class _NativeEmbeddingResponse(BaseModel):
    """Native API 的完整响应。"""

    output: _NativeEmbeddingOutput


class DashScopeEmbeddings(BaseAsyncEmbeddings):
    """DashScope Embedding 客户端。

    特性继承自 BaseAsyncEmbeddings：
    - 连接池管理
    - 自动重试
    - 异步优先
    """

    model: str = "text-embedding-v4"
    base_url: str | None = None
    batch_size: int = 10  # OpenAI compatible mode 最大 10 文本/请求

    @classmethod
    def _get_provider_name(cls) -> str:
        return "DashScope"

    @model_validator(mode="before")
    @classmethod
    def validate_environment(cls, values: JSONDict | None) -> JSONDict | None:
        """验证环境变量。"""
        if values is None:
            return values
        values["api_key"] = EnvUtils.get_from_dict_or_env(values, "api_key", "DASHSCOPE_API_KEY")
        return cast(JSONDict, values)

    def _is_openai_compatible_mode(self) -> bool:
        """判断是否使用 OpenAI 兼容模式。"""
        return self.base_url is not None and "compatible-mode" in self.base_url

    async def _request_embeddings(self, texts: list[str]) -> list[list[float]]:
        """发送 DashScope Embedding 请求。

        根据 base_url 自动选择 API 格式：
        - OpenAI Compatible: POST /embeddings, {"model": "...", "input": [...]}
        - Native API: POST /services/embeddings/..., {"model": "...", "input": {"texts": [...]}}
        """
        client = await self._get_async_client()
        base = self.base_url or _DEFAULT_BASE_URL

        if self._is_openai_compatible_mode():
            url = f"{base}/embeddings"
            body = {
                "model": self.model,
                "input": texts,
            }
        else:
            url = f"{base}/services/embeddings/text-embedding/text-embedding"
            body = {
                "model": self.model,
                "input": {"texts": texts},
                "parameters": {"text_type": "document"},
            }

        response = await client.post(url, json=body)
        response.raise_for_status()

        response_data = cast(JSONDict, response.json())

        if self._is_openai_compatible_mode():
            parsed = _OpenAIEmbeddingResponse.model_validate(response_data)
            sorted_data = sorted(parsed.data, key=lambda x: x.index)
            return [item.embedding for item in sorted_data]

        parsed_native = _NativeEmbeddingResponse.model_validate(response_data)
        sorted_data = sorted(parsed_native.output.embeddings, key=lambda x: x.text_index)
        return [item.embedding for item in sorted_data]
