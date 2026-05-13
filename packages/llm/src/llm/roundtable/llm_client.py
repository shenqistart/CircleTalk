"""OpenAI-compatible LLM client for roundtable generation."""

from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Protocol, cast

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from llm.roundtable.prompts import round_prompt
from llm.roundtable.schema import DecisionArtifact, RoundName, RoundtableLanguage, RoundtableMessage, SelectedPersona, normalize_language


class RoundtableLLMClient(Protocol):
    """Generation contract used by the roundtable orchestrator."""

    def generate_persona_message(
        self,
        *,
        decision_prompt: str,
        selected: SelectedPersona,
        round_name: RoundName,
        prior_messages: list[RoundtableMessage],
        language: RoundtableLanguage = "zh",
    ) -> str:
        """Generate one persona message for one round."""
        ...

    def stream_persona_message(
        self,
        *,
        decision_prompt: str,
        selected: SelectedPersona,
        round_name: RoundName,
        prior_messages: list[RoundtableMessage],
        language: RoundtableLanguage = "zh",
    ) -> AsyncIterator[str]:
        """Stream one persona message for one round."""
        ...

    def synthesize(
        self,
        *,
        decision_prompt: str,
        personas: list[SelectedPersona],
        messages: list[RoundtableMessage],
        language: RoundtableLanguage = "zh",
    ) -> DecisionArtifact:
        """Generate the moderator artifact."""
        ...

    def follow_up(
        self,
        *,
        question: str,
        selected_personas: list[SelectedPersona],
        transcript: list[str],
        artifact: DecisionArtifact | None,
        language: RoundtableLanguage = "zh",
    ) -> str:
        """Generate one follow-up answer."""
        ...

    def stream_follow_up(
        self,
        *,
        question: str,
        selected_personas: list[SelectedPersona],
        transcript: list[str],
        artifact: DecisionArtifact | None,
        language: RoundtableLanguage = "zh",
    ) -> AsyncIterator[str]:
        """Stream one follow-up answer."""
        ...


@dataclass(frozen=True)
class RoundtableLLMConfig:
    """Runtime config for the roundtable LLM path."""

    api_key: str
    model: str
    base_url: str | None = None
    temperature: float = 0.7
    timeout: float = 30.0
    max_tokens: int = 700


def _env_enabled(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def load_roundtable_llm_config() -> RoundtableLLMConfig | None:
    """Load optional LLM config from environment variables."""
    if not _env_enabled(os.getenv("ROUNDTABLE_LLM_ENABLED")):
        return None

    model = (os.getenv("ROUNDTABLE_LLM_MODEL") or "").strip()
    api_key = (os.getenv("ROUNDTABLE_LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()
    if not model or not api_key:
        return None

    base_url = (os.getenv("ROUNDTABLE_LLM_BASE_URL") or "").strip() or None
    return RoundtableLLMConfig(
        api_key=api_key,
        model=model,
        base_url=base_url,
        temperature=_env_float("ROUNDTABLE_LLM_TEMPERATURE", 0.7),
        timeout=_env_float("ROUNDTABLE_LLM_TIMEOUT", 30.0),
        max_tokens=_env_int("ROUNDTABLE_LLM_MAX_TOKENS", 700),
    )


def build_env_roundtable_llm_client() -> RoundtableLLMClient | None:
    """Create an env-configured client, or None when LLM generation is disabled."""
    config = load_roundtable_llm_config()
    if config is None:
        return None
    return OpenAICompatibleRoundtableLLMClient(config)


def _message_content_to_text(content: object) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "\n".join(parts).strip()
    return str(content).strip()


def _message_content_to_delta(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "".join(parts)
    return str(content)


def _json_object_from_text(text: str) -> dict[str, object]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end > start:
        cleaned = cleaned[start : end + 1]
    parsed = json.loads(cleaned)
    if not isinstance(parsed, dict):
        msg = "roundtable synthesis response must be a JSON object"
        raise ValueError(msg)
    return parsed


def _string_list(value: object) -> tuple[str, ...]:
    if isinstance(value, list):
        return tuple(str(item) for item in value if str(item).strip())
    if isinstance(value, tuple):
        return tuple(str(item) for item in value if str(item).strip())
    if isinstance(value, str) and value.strip():
        return (value.strip(),)
    return ()


def _debate_map(value: object) -> tuple[dict[str, str], ...]:
    if not isinstance(value, list):
        return ()
    items: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        persona_name = str(item.get("persona_name") or item.get("personaName") or "")
        position = str(item.get("position") or "")
        key_concern = str(item.get("key_concern") or item.get("keyConcern") or "")
        if persona_name and position:
            items.append({"persona_name": persona_name, "position": position, "key_concern": key_concern})
    return tuple(items)


def _language_instruction(language: RoundtableLanguage) -> str:
    if language == "en":
        return "Output English only. Do not mix in Chinese unless quoting the original user prompt."
    return "输出中文。不要混入英文标签，除非引用用户原文。"


class OpenAICompatibleRoundtableLLMClient:
    """LLM client based on LangChain's OpenAI-compatible chat model."""

    def __init__(self, config: RoundtableLLMConfig) -> None:
        kwargs: dict[str, Any] = {
            "model": config.model,
            "api_key": config.api_key,
            "temperature": config.temperature,
            "timeout": config.timeout,
            "max_tokens": config.max_tokens,
            "max_retries": 1,
        }
        if config.base_url:
            kwargs["base_url"] = config.base_url
        self._model = ChatOpenAI(**cast(Any, kwargs))

    def _invoke(self, system: str, human: str) -> str:
        response = self._model.invoke([SystemMessage(content=system), HumanMessage(content=human)])
        return _message_content_to_text(response.content)

    async def _astream(self, system: str, human: str) -> AsyncIterator[str]:
        async for chunk in self._model.astream([SystemMessage(content=system), HumanMessage(content=human)]):
            text = _message_content_to_delta(chunk.content)
            if text:
                yield text

    def _persona_prompts(
        self,
        *,
        decision_prompt: str,
        selected: SelectedPersona,
        round_name: RoundName,
        prior_messages: list[RoundtableMessage],
        language: RoundtableLanguage = "zh",
    ) -> tuple[str, str]:
        normalized = normalize_language(language)
        persona = selected.persona
        prior = "\n".join(
            f"- {message.persona_name or message.role}({message.round_name}): {message.content}"
            for message in prior_messages[-12:]
        )
        system = (
            f"{persona.prompt}\n"
            "你正在参与一个多人物圆桌决策。必须保持该人物的独特判断方式，避免复述其他人物或模板句。"
            f"{_language_instruction(normalized)}"
            "80 到 140 字，不要使用 Markdown。"
        )
        human = (
            f"决策题：{decision_prompt}\n"
            f"当前轮次：{round_name.value}\n"
            f"轮次任务：{round_prompt(round_name, normalized)}\n"
            f"已出现观点：\n{prior or '暂无'}\n"
            "请给出这一位人物在本轮的发言，必须包含一个具体判断或行动条件。"
        )
        return system, human

    def generate_persona_message(
        self,
        *,
        decision_prompt: str,
        selected: SelectedPersona,
        round_name: RoundName,
        prior_messages: list[RoundtableMessage],
        language: RoundtableLanguage = "zh",
    ) -> str:
        system, human = self._persona_prompts(
            decision_prompt=decision_prompt,
            selected=selected,
            round_name=round_name,
            prior_messages=prior_messages,
            language=language,
        )
        return self._invoke(system, human)

    async def stream_persona_message(
        self,
        *,
        decision_prompt: str,
        selected: SelectedPersona,
        round_name: RoundName,
        prior_messages: list[RoundtableMessage],
        language: RoundtableLanguage = "zh",
    ) -> AsyncIterator[str]:
        system, human = self._persona_prompts(
            decision_prompt=decision_prompt,
            selected=selected,
            round_name=round_name,
            prior_messages=prior_messages,
            language=language,
        )
        async for chunk in self._astream(system, human):
            yield chunk

    def synthesize(
        self,
        *,
        decision_prompt: str,
        personas: list[SelectedPersona],
        messages: list[RoundtableMessage],
        language: RoundtableLanguage = "zh",
    ) -> DecisionArtifact:
        normalized = normalize_language(language)
        persona_names = "、".join(selected.persona.display_name for selected in personas)
        transcript = "\n".join(
            f"- {message.persona_name or message.role}({message.round_name}): {message.content}"
            for message in messages[-18:]
        )
        system = (
            "你是圆桌主持人。请把多人物讨论汇总成严格 JSON，不要输出 JSON 之外的文字。"
            f"{_language_instruction(normalized)}"
            "字段：memo(string), recommendation(string), reasons(string[]), debate_map(array)。"
            "debate_map 每项包含 persona_name, position, key_concern。"
        )
        human = (
            f"决策题：{decision_prompt}\n"
            f"参与人物：{persona_names}\n"
            f"讨论记录：\n{transcript}\n"
            "请输出可被 json.loads 解析的 JSON。"
        )
        raw = self._invoke(system, human)
        parsed = _json_object_from_text(raw)
        memo = str(parsed.get("memo") or "").strip()
        recommendation = str(parsed.get("recommendation") or "").strip()
        reasons = _string_list(parsed.get("reasons"))
        debate_map = _debate_map(parsed.get("debate_map") or parsed.get("debateMap"))
        if not memo or not recommendation or not reasons:
            msg = "roundtable synthesis JSON missing required fields"
            raise ValueError(msg)
        return DecisionArtifact(memo=memo, recommendation=recommendation, reasons=reasons, debate_map=debate_map)

    def follow_up(
        self,
        *,
        question: str,
        selected_personas: list[SelectedPersona],
        transcript: list[str],
        artifact: DecisionArtifact | None,
        language: RoundtableLanguage = "zh",
    ) -> str:
        normalized = normalize_language(language)
        persona_names = "、".join(selected.persona.display_name for selected in selected_personas) or "当前圆桌"
        prior = "\n".join(f"- {item}" for item in transcript[-12:])
        artifact_text = (
            f"memo: {artifact.memo}\nrecommendation: {artifact.recommendation}\nreasons: {', '.join(artifact.reasons)}"
            if artifact
            else "暂无三件套"
        )
        system = f"你是圆桌主持人，负责基于既有讨论回答追问。{_language_instruction(normalized)}120 到 220 字，不要使用 Markdown。"
        human = (
            f"参与人物：{persona_names}\n"
            f"追问：{question}\n"
            f"已有 transcript：\n{prior}\n"
            f"已有三件套：\n{artifact_text}\n"
            "请给出一个可执行的后续建议，并说明它如何继承或修正前面的圆桌意见。"
        )
        return self._invoke(system, human)

    async def stream_follow_up(
        self,
        *,
        question: str,
        selected_personas: list[SelectedPersona],
        transcript: list[str],
        artifact: DecisionArtifact | None,
        language: RoundtableLanguage = "zh",
    ) -> AsyncIterator[str]:
        normalized = normalize_language(language)
        persona_names = "、".join(selected.persona.display_name for selected in selected_personas) or "当前圆桌"
        prior = "\n".join(f"- {item}" for item in transcript[-12:])
        artifact_text = (
            f"memo: {artifact.memo}\nrecommendation: {artifact.recommendation}\nreasons: {', '.join(artifact.reasons)}"
            if artifact
            else "暂无三件套"
        )
        system = f"你是圆桌主持人，负责基于既有讨论回答追问。{_language_instruction(normalized)}120 到 220 字，不要使用 Markdown。"
        human = (
            f"参与人物：{persona_names}\n"
            f"追问：{question}\n"
            f"已有 transcript：\n{prior}\n"
            f"已有三件套：\n{artifact_text}\n"
            "请给出一个可执行的后续建议，并说明它如何继承或修正前面的圆桌意见。"
        )
        async for chunk in self._astream(system, human):
            yield chunk
