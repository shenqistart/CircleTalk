"""Reranker 模型工厂。"""

from core.app_config import LLMModule, core_config
from core.logging import get_logger
from langchain_core.documents import BaseDocumentCompressor

from llm.vector.rerankers.dashscope import DashScopeRerank
from llm.vector.rerankers.volcengine import VolcengineRerank

logger = get_logger(__name__)


def get_reranker_client(top_k: int) -> BaseDocumentCompressor:
    """根据配置获取 Reranker 客户端实例。

    Args:
        top_k: rerank 后返回的文档数量。

    Returns:
        配置好的 BaseDocumentCompressor 实例。

    Raises:
        ValueError: 不支持的 Reranker 提供商。
    """
    rerank_config = core_config.get_llm_module_config(LLMModule.RERANK)
    provider = rerank_config.provider
    model_name = rerank_config.model_name

    if provider == "dashscope":
        # DashScope Rerank 仅支持 Native API，使用 vector_url
        api_url, api_key = core_config.get_provider_config(provider, use_vector_url=True)
        logger.debug("[RERANK] DashScope: model=%s, top_k=%d", model_name, top_k)
        return DashScopeRerank(api_key=api_key, base_url=api_url, model=model_name, top_n=top_k)

    if provider == "volcengine":
        # Volcengine 需要 vector_url
        api_url, api_key = core_config.get_provider_config(provider, use_vector_url=True)
        logger.debug("[RERANK] Volcengine: model=%s, top_k=%d", model_name, top_k)
        return VolcengineRerank(api_key=api_key, base_url=api_url, model=model_name, top_n=top_k)

    msg = f"不支持的 Reranker 提供商: '{provider}'"
    raise ValueError(msg)
