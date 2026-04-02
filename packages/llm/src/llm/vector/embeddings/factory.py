"""Embedding 模型工厂，根据配置动态创建并缓存 Embedding 实例。"""

from typing import Any

from core.app_config import LLMModule, core_config
from core.logging import get_logger
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.embeddings import Embeddings

from llm.vector.embeddings.dashscope import DashScopeEmbeddings
from llm.vector.embeddings.volcengine import VolcengineEmbeddings

logger = get_logger(__name__)
_embedding_cache: dict[tuple[str, str, str], Embeddings] = {}


def get_embedding_client() -> Embeddings:
    """根据当前租户的配置，获取一个 Embedding 模型客户端实例。

    该函数会缓存并复用实例，以避免不必要的重复创建。

    Returns:
        The embedding client instance.

    Raises:
        ValueError: If the provider or model is not supported.
    """
    embedding_config = core_config.get_llm_module_config(LLMModule.EMBEDDING)
    provider = embedding_config.provider
    model_name = embedding_config.model_name
    timeout = embedding_config.timeout
    cache_key = (core_config.current_tenant_name, provider, model_name)
    if cache_key in _embedding_cache:
        logger.debug("[EMBEDDING] Cache hit: provider=%s, model=%s", provider, model_name)
        return _embedding_cache[cache_key]
    logger.info("[EMBEDDING] Creating instance: provider=%s, model=%s", provider, model_name)
    use_vector_url = provider in ("volcengine", "dashscope")
    api_url, api_key = core_config.get_provider_config(provider, use_vector_url=use_vector_url)
    if provider == "dashscope":
        dashscope_kwargs: dict[str, Any] = {"model": model_name, "api_key": api_key, "base_url": api_url}
        if timeout is not None:
            dashscope_kwargs["request_timeout"] = float(timeout)
        embedding_client = DashScopeEmbeddings(**dashscope_kwargs)
    elif provider == "ollama":
        if not api_url:
            msg = "Ollama 提供商未配置有效的基础地址，无法创建 Embedding 实例。"
            raise ValueError(msg)
        embedding_client = OllamaEmbeddings(model=model_name, base_url=api_url)
    elif provider == "volcengine":
        volcengine_kwargs: dict[str, Any] = {"model": model_name, "api_key": api_key, "base_url": api_url}
        if timeout is not None:
            volcengine_kwargs["request_timeout"] = float(timeout)
        embedding_client = VolcengineEmbeddings(**volcengine_kwargs)
    else:
        msg = f"不支持的Embedding提供商: '{provider}'"
        raise ValueError(msg)
    _embedding_cache[cache_key] = embedding_client
    logger.debug("[EMBEDDING] Cached instance: provider=%s, model=%s", provider, model_name)
    return embedding_client
