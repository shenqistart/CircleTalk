"""火山引擎 Rerank 客户端（异步实现）。

基于火山云搜索服务 (Volcengine) 的 Rerank 文档压缩器。
使用 api_key 进行认证。

重构说明：
- 原实现使用 requests 同步库，在异步上下文中调用会阻塞事件循环
- 现改为继承 BaseAsyncReranker，使用 httpx.AsyncClient 实现真正的异步
"""

from __future__ import annotations

from typing import cast

from core.logging import get_logger
from core.type.common import JSONDict
from core.utils.env import EnvUtils
from pydantic import model_validator

from llm.vector.rerankers.base import BaseAsyncReranker, RerankResult

logger = get_logger(__name__)


class VolcengineRerank(BaseAsyncReranker):
    """基于火山云搜索服务的 Rerank 文档压缩器（异步版本）。"""

    top_n: int = 3
    model: str = "BAAI/bge-reranker-v2-m3"
    api_key: str | None = None
    base_url: str | None = None

    @classmethod
    def _get_provider_name(cls) -> str:
        return "Volcengine"

    @model_validator(mode="before")
    @classmethod
    def validate_environment(cls, values: JSONDict | None) -> JSONDict | None:
        """验证环境变量。"""
        if values is None:
            return None
        values["api_key"] = EnvUtils.get_from_dict_or_env(values, "api_key", "VOLCENGINE_VECTOR_KEY")
        values["base_url"] = EnvUtils.get_from_dict_or_env(values, "base_url", "VOLCENGINE_VECTOR_URL")
        return values

    async def _request_rerank(self, query: str, documents: list[str]) -> list[RerankResult]:
        """发送火山引擎 Rerank 请求（异步）。"""
        if not self.base_url:
            msg = "VolcengineRerank 需要配置 base_url (环境变量 VOLCENGINE_VECTOR_URL)"
            raise ValueError(msg)

        client = await self._get_async_client()
        url = f"{self.base_url}/rerank"
        body: JSONDict = {
            "model": self.model,
            "query": query,
            "documents": documents,
            "top_n": self.top_n,
        }

        response = await client.post(url, json=body)
        response.raise_for_status()

        response_data = cast(JSONDict, response.json())
        results = response_data.get("results", [])

        if not isinstance(results, list):
            return []

        return [
            RerankResult(index=r["index"], relevance_score=r["relevance_score"])
            for r in results
            if isinstance(r, dict) and "index" in r and "relevance_score" in r
        ]
