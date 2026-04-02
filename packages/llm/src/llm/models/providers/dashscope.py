"""DashScope (阿里云) 提供商，基于 BaseChatOpenAI + OpenAI-compatible API。"""

from __future__ import annotations

import json
import re
from collections.abc import AsyncIterator, Iterator, Sequence
from json import JSONDecodeError
from typing import Any

from core.app_config import LLMModuleConfig
from langchain_core.callbacks import AsyncCallbackManagerForLLMRun, CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessageChunk, BaseMessage
from langchain_core.outputs import ChatGenerationChunk
from langchain_core.utils.utils import secret_from_env
from langchain_openai.chat_models.base import BaseChatOpenAI
from pydantic import Field, SecretStr


def _try_repair_json(raw: str) -> str | None:
    """尝试修复畸形 JSON 字符串，成功返回合法 JSON，失败返回 None。"""
    try:
        json.loads(raw)
    except (JSONDecodeError, ValueError):
        pass
    else:
        return raw
    try:
        cleaned = re.sub(r",\s*([}\]])", r"\1", raw)
        parsed = json.loads(cleaned)
        return json.dumps(parsed)
    except Exception:
        return None


def _parse_args(args_value: str | None) -> dict[str, object] | None:
    """解析 invalid_tool_call 的 args，返回字典或 None（跳过）。"""
    if not args_value:
        return {}
    repaired = _try_repair_json(args_value)
    if repaired is None:
        return None
    return json.loads(repaired)


def _repair_tool_call_chunks(msg: AIMessageChunk) -> None:
    """修复 tool_call_chunks 中畸形的 args JSON。"""
    if not msg.tool_call_chunks:
        return
    for tc_chunk in msg.tool_call_chunks:
        raw = tc_chunk.get("args")
        if not (isinstance(raw, str) and raw):
            continue
        repaired = _try_repair_json(raw)
        if repaired is not None:
            tc_chunk["args"] = repaired


def _repair_invalid_tool_calls(msg: AIMessageChunk, chunk: ChatGenerationChunk) -> None:
    """最后一个 chunk：将 invalid_tool_calls 修复为 tool_calls。"""
    is_final = chunk.generation_info and chunk.generation_info.get("finish_reason")
    if not (is_final and msg.invalid_tool_calls):
        return
    for invalid_tc in msg.invalid_tool_calls:
        parsed_args = _parse_args(invalid_tc.get("args"))
        if parsed_args is None:
            continue
        msg.tool_calls.append(
            {
                "id": invalid_tc.get("id") or "",
                "name": invalid_tc.get("name") or "",
                "args": parsed_args,
                "type": "tool_call",
            }
        )
    msg.invalid_tool_calls = []


def _repair_stream_chunk(chunk: ChatGenerationChunk) -> ChatGenerationChunk:
    """修复单个 streaming chunk 中的畸形 tool_call_chunks 和 invalid_tool_calls。"""
    if not isinstance(chunk.message, AIMessageChunk):
        return chunk
    _repair_tool_call_chunks(chunk.message)
    _repair_invalid_tool_calls(chunk.message, chunk)
    return chunk


def _normalize_tool_call_chunks(chunks: Sequence[Any], last_named_index: int) -> int:
    """归一化 tool_call_chunks 的 index 和 id，返回更新后的 last_named_index。

    修复 DashScope/Qwen3 流式 tool_call 的两个问题：

    1. Index 不一致：首个 chunk 返回 index=N + name，续传 chunk 返回 index=0，
       导致 LangChain merge_lists 按 index 匹配时拆成两个独立 tool_call。

    2. ID 不兼容：续传 chunk 的 id="" (空字符串)，merge_lists 要求
       ``e_left.id is None OR e.id is None OR e_left.id == e.id``，
       空字符串 ≠ None 导致即使 index 相同也拒绝合并。

    额外处理：如果命名 chunk 的 args="{}" 且同一事件中存在续传 chunk，
    清空命名 chunk 的 args 以避免合并后产生 "{}{"real":"args"}" 的畸形 JSON。

    参考: https://github.com/langchain-ai/langchain/issues/31511
    """
    has_continuation = False
    for tc in chunks:
        if tc.get("name"):
            idx = tc.get("index")
            if idx is not None:
                last_named_index = idx
            else:
                tc["index"] = last_named_index
        else:
            has_continuation = True
            if tc.get("index") != last_named_index:
                tc["index"] = last_named_index
            # 清空空字符串 id → None，让 merge_lists 的 "id is None" 条件通过
            if not tc.get("id"):
                tc["id"] = None

    # 命名 chunk 的 args="{}" 是 DashScope 的 split 产物，不是真正的空参数
    # 清空为 "" 以避免合并后拼接成 "{}{"query":"..."}" 畸形 JSON
    if has_continuation:
        for tc in chunks:
            if tc.get("name") and tc.get("args") == "{}":
                tc["args"] = ""

    return last_named_index


class _DashScopeChatModel(BaseChatOpenAI):
    """BaseChatOpenAI 子类，适配 DashScope OpenAI-compatible API。

    - openai_api_key 回退到 DASHSCOPE_API_KEY 环境变量
    - _stream()/_astream() 修复畸形 JSON args、invalid_tool_calls 和 tool_call_chunks index 不一致
    """

    openai_api_key: SecretStr | None = Field(
        alias="api_key",
        default_factory=secret_from_env("DASHSCOPE_API_KEY", default=None),
    )

    def _stream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        *,
        stream_usage: bool | None = None,
        **kwargs: object,
    ) -> Iterator[ChatGenerationChunk]:
        last_named_index: int = 0
        for chunk in super()._stream(messages, stop=stop, run_manager=run_manager, stream_usage=stream_usage, **kwargs):
            _repair_stream_chunk(chunk)
            if isinstance(chunk.message, AIMessageChunk) and chunk.message.tool_call_chunks:
                last_named_index = _normalize_tool_call_chunks(chunk.message.tool_call_chunks, last_named_index)
            yield chunk

    async def _astream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        *,
        stream_usage: bool | None = None,
        **kwargs: object,
    ) -> AsyncIterator[ChatGenerationChunk]:
        last_named_index: int = 0
        async for chunk in super()._astream(
            messages, stop=stop, run_manager=run_manager, stream_usage=stream_usage, **kwargs
        ):
            _repair_stream_chunk(chunk)
            if isinstance(chunk.message, AIMessageChunk) and chunk.message.tool_call_chunks:
                last_named_index = _normalize_tool_call_chunks(chunk.message.tool_call_chunks, last_named_index)
            yield chunk


class DashScopeProvider:
    """DashScope 提供商。

    使用 _DashScopeChatModel（BaseChatOpenAI 子类）通过 OpenAI-compatible API 对接：
    - Streaming tool call 畸形 JSON 修复
    - Streaming tool_call_chunks index 归一化（Qwen3 index 不一致问题）
    - 始终关闭 thinking（Qwen3 thinking 与 streaming tool calling 不兼容）

    已知问题参考:
    - https://github.com/langchain-ai/langchain/issues/31511
    - https://pypi.org/project/langchain-qwq/ (ChatQwQ._generate 中的 chunks_by_index 逻辑)
    """

    def create_model(
        self,
        module_config: LLMModuleConfig,
        api_url: str,
        api_key: str,
        callbacks: list[Any] | None = None,
    ) -> BaseChatModel:
        kwargs: dict[str, Any] = {
            "model": module_config.model_name,
            "max_tokens": module_config.max_tokens,
            "timeout": module_config.timeout,
            "max_retries": 2,
            "callbacks": callbacks,
            # thinking 与 streaming tool calling 不兼容，始终关闭
            "extra_body": {"enable_thinking": False},
        }
        if api_key:
            kwargs["api_key"] = api_key
        if api_url:
            kwargs["base_url"] = api_url
        if module_config.temperature is not None:
            kwargs["temperature"] = module_config.temperature
        return _DashScopeChatModel(**kwargs)
