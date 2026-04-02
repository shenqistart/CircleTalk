"""Chat Model Provider 协议定义。"""

from __future__ import annotations

from typing import Any, Protocol

from core.app_config import LLMModuleConfig
from langchain_core.language_models import BaseChatModel


class ChatModelProvider(Protocol):
    """LLM Chat Model 提供商协议。

    每个提供商实现此协议，处理自身特有的模型创建逻辑。
    返回的 BaseChatModel 对消费方透明。
    """

    def create_model(
        self,
        module_config: LLMModuleConfig,
        api_url: str,
        api_key: str,
        callbacks: list[Any] | None = None,
    ) -> BaseChatModel: ...
