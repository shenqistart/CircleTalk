"""LLM 客户端工厂，负责创建和管理多租户的 LLM 模型实例。

通过 providers 模块路由到各 Provider 实现创建 Chat Model。
"""

from __future__ import annotations

from typing import Any, cast

import httpx
from core.app_config import LLMModule, LLMModuleConfig, TenantConfig, core_config
from core.context import request_context
from core.context.request import RequestContextParams
from core.logging import get_logger
from langchain_core.language_models import BaseChatModel
from langchain_openai.chat_models.base import BaseChatOpenAI
from openai import APIConnectionError, APITimeoutError, RateLimitError

from llm.models.callbacks import LoggingCallbackHandler
from llm.models.providers import create_chat_model
from llm.observability import configure_langsmith_tracing

logger = get_logger(__name__)
TenantStore = dict[str, BaseChatModel]
_chat_models: dict[str, TenantStore] = {}


def _initialize_module_client(module_name: str, module_config: LLMModuleConfig, tenant_store: TenantStore) -> None:
    callbacks: list[Any] = [LoggingCallbackHandler(model_name=module_config.model_name)]
    api_url, api_key = core_config.get_provider_config(module_config.provider)
    client = create_chat_model(module_config.provider, module_config, api_url, api_key, callbacks)

    # BaseChatOpenAI 及其子类（ChatOpenAI）自带 max_retries，无需额外 retry 包装
    if isinstance(client, BaseChatOpenAI):
        tenant_store[module_name] = client
        return

    # 其他模型类型（如 Ollama）需要手动 retry 包装
    tenant_store[module_name] = cast(
        BaseChatModel,
        client.with_retry(
            retry_if_exception_type=(
                APITimeoutError,
                APIConnectionError,
                RateLimitError,
                httpx.ReadError,
                httpx.ConnectError,
            ),
            wait_exponential_jitter=True,
            stop_after_attempt=3,
        ),
    )


def _initialize_tenant(tenant_name: str, tenant_config: TenantConfig, tenant_idx: int, tenant_count: int) -> None:
    logger.info("Initializing tenant: [%d/%d] %s", tenant_idx, tenant_count, tenant_name)
    request_context.set_request_context(RequestContextParams(tenant=tenant_name, username="system_init"))
    tenant_store: TenantStore = {}
    _chat_models[tenant_name] = tenant_store
    llm_modules = tenant_config.llm_modules
    if not llm_modules:
        logger.warning("Tenant %s has no llm_modules, skipping", tenant_name)
        return
    module_count = len(llm_modules)
    for module_idx, (module_enum, module_config) in enumerate(llm_modules.items(), 1):
        module_name = module_enum.value
        logger.info(
            "Creating module: [%d/%d] %s (%s/%s)",
            module_idx,
            module_count,
            module_name,
            module_config.provider,
            module_config.model_name,
        )
        _initialize_module_client(module_name, module_config, tenant_store)
        logger.debug("Module ready: %s", module_name)


def initialize_chat_models_sync() -> None:
    configure_langsmith_tracing()
    tenant_items = list(core_config.tenants.items())
    tenant_count = len(tenant_items)
    for tenant_idx, (tenant_name, tenant_config) in enumerate(tenant_items, 1):
        _initialize_tenant(tenant_name, tenant_config, tenant_idx, tenant_count)


async def initialize_chat_models() -> None:
    logger.info("Initializing for all tenants...")
    try:
        initialize_chat_models_sync()
        logger.info("All models initialized")
    finally:
        request_context.clear_request_context()


def get_chat_model(module: LLMModule) -> BaseChatModel:
    tenant = core_config.current_tenant_name
    module_name = module.value
    tenant_clients = _chat_models.get(tenant)
    if not tenant_clients:
        logger.error("Model not found for tenant: %s, available=%s", tenant, list(_chat_models.keys()))
        msg = f"当前租户 '{tenant}' 没有找到对应的聊天模型实例。"
        raise ValueError(msg)
    if not (client := tenant_clients.get(module_name)):
        available_modules = list(tenant_clients.keys())
        logger.error(
            "Module not found: module=%s, tenant=%s, available=%s",
            module_name,
            tenant,
            available_modules,
        )
        msg = f"租户 '{tenant}' 的模块 '{module_name}' 没有找到对应的聊天模型实例。"
        raise ValueError(msg)
    return client


def get_fast_model() -> BaseChatModel:
    """获取 FAST 轻量模型，未配置时自动降级到 CHAT 模型。"""
    try:
        return get_chat_model(LLMModule.FAST)
    except ValueError:
        logger.warning("FAST model unavailable, falling back to CHAT")
        return get_chat_model(LLMModule.CHAT)
