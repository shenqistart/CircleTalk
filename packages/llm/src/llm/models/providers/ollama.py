"""Ollama 本地模型提供商。"""

from __future__ import annotations

from typing import Any

from core.app_config import LLMModuleConfig
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel


class OllamaProvider:
    """Ollama 本地模型提供商。"""

    def create_model(
        self,
        module_config: LLMModuleConfig,
        api_url: str,
        api_key: str,
        callbacks: list[Any] | None = None,
    ) -> BaseChatModel:
        return init_chat_model(
            model=module_config.model_name,
            model_provider="ollama",
            base_url=api_url,
            temperature=module_config.temperature,
            num_predict=module_config.max_tokens,
            timeout=module_config.timeout,
            callbacks=callbacks,
        )
