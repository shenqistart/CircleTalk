"""Chat Model Provider 路由。

根据 provider 名称分发到对应的 ChatModelProvider 实现。
"""

from __future__ import annotations

from typing import Any

from core.app_config import LLMModuleConfig
from langchain_core.language_models import BaseChatModel

from .base import ChatModelProvider
from .dashscope import DashScopeProvider
from .ollama import OllamaProvider
from .openai_compatible import OpenAICompatibleProvider

_PROVIDER_REGISTRY: dict[str, ChatModelProvider] = {
    "dashscope": DashScopeProvider(),
    "openai": OpenAICompatibleProvider(),
    "deepseek": OpenAICompatibleProvider(),
    "volcengine": OpenAICompatibleProvider(),
    "ollama": OllamaProvider(),
}


def create_chat_model(
    provider_name: str,
    module_config: LLMModuleConfig,
    api_url: str,
    api_key: str,
    callbacks: list[Any] | None = None,
) -> BaseChatModel:
    """根据 provider 路由到对应实现创建 Chat Model。"""
    provider = _PROVIDER_REGISTRY.get(provider_name)
    if provider is None:
        supported = ", ".join(sorted(_PROVIDER_REGISTRY.keys()))
        msg = f"Unsupported LLM provider: '{provider_name}'. Supported: {supported}"
        raise ValueError(msg)
    return provider.create_model(module_config, api_url, api_key, callbacks)
