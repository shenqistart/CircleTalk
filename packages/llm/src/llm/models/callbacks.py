"""自定义LangChain回调处理器，用于提供统一的日志记录功能。"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import override
from uuid import UUID

from core.logging import get_logger
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.outputs import LLMResult

logger = get_logger(__name__)

_LLM_RESPONSE_PREVIEW_LIMIT = 250
TokenValue = str | int | float | bool | None


SerializedPayload = dict[str, object]


def _token_value(value: TokenValue) -> str | int:
    """将 token 计数转换为可日志记录的值。"""
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    if value is None:
        return "N/A"
    return str(value)


def _extract_token_usage(llm_output: Mapping[str, object] | None) -> tuple[str | int, str | int, str | int]:
    """提取 token 使用统计.

    DashScope 流式模式仅返回 total_tokens，此时 prompt/completion 返回 "N/A"。
    """
    if llm_output:
        usage_raw = llm_output.get("token_usage")
        if isinstance(usage_raw, Mapping):
            prompt_tokens = _token_value(usage_raw.get("prompt_tokens"))
            completion_tokens = _token_value(usage_raw.get("completion_tokens"))
            total_tokens = _token_value(usage_raw.get("total_tokens"))
            return (prompt_tokens, completion_tokens, total_tokens)
    return ("N/A", "N/A", "N/A")


def _format_token_string(prompt: str | int, completion: str | int, total: str | int) -> str:
    """构建 token 日志字符串，跳过 N/A 字段."""
    parts: list[str] = []
    if prompt != "N/A":
        parts.append(f"prompt={prompt}")
    if completion != "N/A":
        parts.append(f"completion={completion}")
    if total != "N/A":
        parts.append(f"total={total}")
    return ", ".join(parts) if parts else "N/A"


def _ensure_mapping(value: object | None) -> Mapping[str, object] | None:
    """将任意对象安全转换为映射。"""
    if isinstance(value, Mapping):
        return value
    return None


class LoggingCallbackHandler(AsyncCallbackHandler):
    """用于记录LLM调用信息的自定义回调处理器。"""

    def __init__(self, model_name: str = "unknown") -> None:
        super().__init__()
        self._request_count = 0
        self.model_name = model_name

    @override
    async def on_llm_start(
        self,
        serialized: SerializedPayload,
        prompts: list[str],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: SerializedPayload | None = None,
        **kwargs: object,
    ) -> None:
        self._request_count += 1
        invocation_params = _ensure_mapping(kwargs.get("invocation_params")) or {}
        model_info = _ensure_mapping(serialized.get("kwargs")) or {}
        temperature = invocation_params.get("temperature") or model_info.get("temperature") or "default"
        logger.info(
            "Call started: count=%d, run_id=%s, model=%s, temperature=%s",
            self._request_count,
            run_id,
            self.model_name,
            temperature,
        )

    @override
    async def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: object,
    ) -> None:
        llm_output_raw = getattr(response, "llm_output", None)
        prompt_tokens, completion_tokens, total_tokens = _extract_token_usage(_ensure_mapping(llm_output_raw))
        token_str = _format_token_string(prompt_tokens, completion_tokens, total_tokens)
        logger.info(
            "Call ended: count=%d, run_id=%s, tokens=(%s)",
            self._request_count,
            run_id,
            token_str,
        )
        if response.generations and response.generations[0]:
            generation = response.generations[0][0]
            text = generation.text or ""
            preview = text[:_LLM_RESPONSE_PREVIEW_LIMIT]
            if len(text) > _LLM_RESPONSE_PREVIEW_LIMIT:
                preview += "..."
            logger.debug("Response preview: %s", preview)

    @override
    async def on_chain_start(
        self,
        serialized: SerializedPayload,
        inputs: SerializedPayload,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: SerializedPayload | None = None,
        **kwargs: object,
    ) -> None:
        chain_name_obj = serialized.get("name")
        if isinstance(chain_name_obj, str):
            chain_name = chain_name_obj
        else:
            serialized_id = serialized.get("id")
            chain_name = str(serialized_id[-1]) if isinstance(serialized_id, list) and serialized_id else "<unknown>"
        logger.info("Chain started: run_id=%s, name=%s", run_id, chain_name)
        logger.debug("Chain inputs: %s", inputs)

    @override
    async def on_chain_end(
        self,
        outputs: SerializedPayload,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: object,
    ) -> None:
        logger.info("Chain ended: run_id=%s", run_id)
        logger.debug("Chain outputs: %s", outputs)

    @override
    async def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: object,
    ) -> None:
        if isinstance(error, asyncio.CancelledError):
            logger.info("Call cancelled: run_id=%s", run_id)
        else:
            logger.error("Call error: run_id=%s, error=%s", run_id, error, exc_info=error)
