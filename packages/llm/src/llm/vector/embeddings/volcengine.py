"""火山引擎 Embedding 客户端。

继承 BaseAsyncEmbeddings，实现火山引擎特定的 API 调用逻辑。
"""

from __future__ import annotations

from typing import cast

from core.logging import get_logger
from core.type.common import JSONDict
from core.utils.env import EnvUtils
from pydantic import BaseModel, model_validator

from llm.vector.embeddings.base import BaseAsyncEmbeddings

logger = get_logger(__name__)


class _EmbeddingItem(BaseModel):
    """Embedding API 响应中的单条数据。"""

    embedding: list[float]
    index: int
    object: str


class _EmbeddingResponse(BaseModel):
    """Embedding API 完整响应。"""

    data: list[_EmbeddingItem]


class VolcengineEmbeddings(BaseAsyncEmbeddings):
    """火山引擎 Embedding 客户端。

    特性继承自 BaseAsyncEmbeddings：
    - 连接池管理
    - 自动重试
    - 异步优先
    """

    model: str = "BAAI/bge-m3"
    batch_size: int = 20  # 火山引擎支持更大批量

    @classmethod
    def _get_provider_name(cls) -> str:
        return "Volcengine"

    @model_validator(mode="before")
    @classmethod
    def validate_environment(cls, values: JSONDict | None) -> JSONDict | None:
        """验证环境变量。"""
        if values is None:
            return values
        values["api_key"] = EnvUtils.get_from_dict_or_env(values, "api_key", "VOLCENGINE_VECTOR_KEY")
        values["base_url"] = EnvUtils.get_from_dict_or_env(values, "base_url", "VOLCENGINE_VECTOR_URL")
        return cast(JSONDict, values)

    async def _request_embeddings(self, texts: list[str]) -> list[list[float]]:
        """发送火山引擎 Embedding 请求。

        火山引擎 API 格式：
        - 请求: {"model": "...", "input": [...]}
        - 响应: {"data": [{"embedding": [...], "index": 0, "object": "..."}, ...]}
        """
        client = await self._get_async_client()
        url = f"{self.base_url}/embeddings"
        body = {"model": self.model, "input": texts}

        response = await client.post(url, json=body)
        response.raise_for_status()

        response_data = cast(JSONDict, response.json())
        parsed = _EmbeddingResponse.model_validate(response_data)
        sorted_data = sorted(parsed.data, key=lambda x: x.index)
        return [item.embedding for item in sorted_data]
