"""DashScope Rerank 客户端（异步实现）。

支持两种模型：
- gte-rerank-v2：中国区，使用 input/parameters 嵌套格式
- qwen3-rerank：国际区，使用扁平格式

API 端点:
- 中国区: POST https://dashscope.aliyuncs.com/api/v1/services/rerank/text-rerank/text-rerank
- 国际区: POST https://dashscope-intl.aliyuncs.com/compatible-api/v1/reranks
"""

from __future__ import annotations

from typing import cast

from core.logging import get_logger
from core.type.common import JSONDict
from core.utils.env import EnvUtils
from pydantic import model_validator

from llm.vector.rerankers.base import BaseAsyncReranker, RerankResult

logger = get_logger(__name__)

# 国际区模型列表（使用扁平请求格式）
_INTL_MODELS = frozenset({"qwen3-rerank"})

# 默认端点常量（base_url 为 None 时回退到公网默认值）
_DEFAULT_CN_BASE_URL = "https://dashscope.aliyuncs.com/api/v1"
_DEFAULT_INTL_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-api/v1"
_CN_RERANK_PATH = "/services/rerank/text-rerank/text-rerank"
_INTL_RERANK_PATH = "/reranks"


class DashScopeRerank(BaseAsyncReranker):
    """DashScope Rerank 客户端（异步版本）。

    仅支持 Native API，不支持 OpenAI 兼容模式。
    自动根据模型名选择正确的 API 端点和请求格式。
    """

    top_n: int = 3
    model: str = "gte-rerank-v2"
    api_key: str | None = None
    base_url: str | None = None

    @classmethod
    def _get_provider_name(cls) -> str:
        return "DashScope"

    @model_validator(mode="before")
    @classmethod
    def validate_environment(cls, values: JSONDict | None) -> JSONDict | None:
        """验证环境变量。"""
        if values is None:
            return None
        values["api_key"] = EnvUtils.get_from_dict_or_env(values, "api_key", "DASHSCOPE_API_KEY")
        return values

    def _is_intl_model(self) -> bool:
        """判断是否为国际区模型。"""
        return self.model in _INTL_MODELS

    def _get_api_url(self) -> str:
        """根据模型获取正确的 API 端点。"""
        if self._is_intl_model():
            # 国际区模型使用独立端点，不受 base_url 配置影响
            return f"{_DEFAULT_INTL_BASE_URL}{_INTL_RERANK_PATH}"
        base = self.base_url or _DEFAULT_CN_BASE_URL
        return f"{base}{_CN_RERANK_PATH}"

    def _build_request_body(self, query: str, documents: list[str]) -> JSONDict:
        """根据模型构建正确的请求体格式。"""
        if self._is_intl_model():
            # 国际区 qwen3-rerank：扁平格式
            return {
                "model": self.model,
                "documents": documents,
                "query": query,
                "top_n": self.top_n,
            }
        # 中国区 gte-rerank-v2：嵌套格式
        return {
            "model": self.model,
            "input": {
                "query": query,
                "documents": documents,
            },
            "parameters": {
                "top_n": self.top_n,
                "return_documents": False,
            },
        }

    async def _request_rerank(self, query: str, documents: list[str]) -> list[RerankResult]:
        """发送 DashScope Rerank 请求。"""
        client = await self._get_async_client()
        url = self._get_api_url()
        body = self._build_request_body(query, documents)

        logger.debug("[DashScope Rerank] URL=%s, model=%s, docs=%d", url, self.model, len(documents))

        response = await client.post(url, json=body)
        response.raise_for_status()

        response_data = cast(JSONDict, response.json())

        # 国际区和中国区的响应格式相同
        output = response_data.get("output", {})
        results = output.get("results", []) if isinstance(output, dict) else []

        if not isinstance(results, list):
            return []

        return [
            RerankResult(index=r["index"], relevance_score=r["relevance_score"])
            for r in results
            if isinstance(r, dict) and "index" in r and "relevance_score" in r
        ]
