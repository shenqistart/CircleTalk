"""VLM 配置工厂，为 Docling VLM Pipeline 构建 API 配置。

Docling 不支持 LangChain 集成，需要直接调用 OpenAI 兼容的 HTTP API。
本工厂封装配置构建逻辑，复用 core_config 的 Provider 体系。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from core.app_config import LLMModule, LLMModuleConfig, core_config
from core.logging import get_logger
from pydantic import AnyUrl

if TYPE_CHECKING:
    from docling.datamodel.pipeline_options_vlm_model import ApiVlmOptions, ResponseFormat

logger = get_logger(__name__)

# 标记是否已初始化全局设置
_docling_settings_initialized = False

# OpenAI 兼容接口的 Provider（使用标准 /chat/completions 路径）
_OPENAI_COMPATIBLE_PROVIDERS = {"openai", "dashscope", "deepseek", "volcengine"}

# 默认 VLM Prompt
DEFAULT_VLM_PROMPT = """Convert this document page to Markdown format.
Extract all text, tables, and structure accurately.
Preserve headings hierarchy using # syntax.
Format tables using Markdown table syntax.
Keep the original language of the document."""


def configure_docling_performance(page_batch_size: int | None = None) -> None:
    """配置 Docling 全局性能参数。

    Docling 默认 page_batch_size=4，对于远程 VLM API 场景过小。
    此函数应在首次创建 DocumentConverter 前调用。

    Args:
        page_batch_size: 页面批处理大小，默认使用 VLM concurrency_limit

    """
    global _docling_settings_initialized  # noqa: PLW0603

    if _docling_settings_initialized:
        return

    from docling.datamodel.settings import settings as docling_settings

    vlm_config = core_config.get_llm_module_config(LLMModule.VLM)
    batch_size = page_batch_size or vlm_config.concurrency_limit or 10

    docling_settings.perf.page_batch_size = batch_size
    _docling_settings_initialized = True

    logger.info("Docling 全局性能配置: page_batch_size=%d", batch_size)


def _build_api_url(base_url: str, provider: str) -> str:
    """根据 Provider 构建完整的 API URL。

    OpenAI 兼容的 Provider 统一使用 /chat/completions 路径。
    """
    base_url = base_url.rstrip("/")

    if provider in _OPENAI_COMPATIBLE_PROVIDERS:
        return f"{base_url}/chat/completions"

    if provider == "ollama":
        return f"{base_url}/api/chat"

    # 未知 provider，假设使用 OpenAI 兼容路径
    logger.warning("未知 VLM provider '%s'，使用默认 /chat/completions 路径", provider)
    return f"{base_url}/chat/completions"


def get_vlm_api_options(
    prompt: str | None = None,
    response_format: ResponseFormat | None = None,
) -> ApiVlmOptions:
    """获取 Docling VLM Pipeline 所需的 API 配置。

    从 config.yaml 读取 VLM 模块配置，构建 ApiVlmOptions。
    支持所有 OpenAI 兼容的 Provider。

    Args:
        prompt: 自定义 VLM 提示词，默认使用 DEFAULT_VLM_PROMPT
        response_format: 响应格式，默认 Markdown

    Returns:
        Docling ApiVlmOptions 配置对象

    """
    from docling.datamodel.pipeline_options_vlm_model import ApiVlmOptions as _ApiVlmOptions
    from docling.datamodel.pipeline_options_vlm_model import ResponseFormat as _ResponseFormat

    if response_format is None:
        response_format = _ResponseFormat.MARKDOWN

    vlm_config: LLMModuleConfig = core_config.get_llm_module_config(LLMModule.VLM)
    provider = vlm_config.provider

    # 获取 Provider 的 API URL 和 Key
    api_url, api_key = core_config.get_provider_config(provider)

    # 构建完整的 API endpoint URL
    full_url = _build_api_url(api_url, provider)

    # 构建认证头
    headers: dict[str, str] = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    api_options = _ApiVlmOptions(
        url=AnyUrl(full_url),
        headers=headers,
        params={
            "model": vlm_config.model_name,
            "max_tokens": vlm_config.max_tokens,
        },
        temperature=vlm_config.temperature,
        timeout=float(vlm_config.timeout or 180),
        concurrency=vlm_config.concurrency_limit or 10,
        prompt=prompt or DEFAULT_VLM_PROMPT,
        response_format=response_format,
    )

    logger.info(
        "VLM 配置: provider=%s, model=%s, url=%s",
        provider,
        vlm_config.model_name,
        full_url,
    )

    return api_options
