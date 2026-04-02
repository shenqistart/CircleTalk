"""OpenAI 兼容协议提供商（OpenAI、DeepSeek、VolcEngine）。"""

from __future__ import annotations

from typing import Any

from core.app_config import LLMModuleConfig
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel


class OpenAICompatibleProvider:
    """OpenAI 兼容 API 提供商。

    使用 LangChain init_chat_model(model_provider="openai") 创建模型，
    通过 base_url 切换不同 Provider 的 endpoint。
    """

    def create_model(
        self,
        module_config: LLMModuleConfig,
        api_url: str,
        api_key: str,
        callbacks: list[Any] | None = None,
    ) -> BaseChatModel:
        return init_chat_model(
            model=module_config.model_name,
            model_provider="openai",
            base_url=api_url,
            api_key=api_key,
            temperature=module_config.temperature,
            max_tokens=module_config.max_tokens,
            timeout=module_config.timeout,
            max_retries=2,
            callbacks=callbacks,
        )
