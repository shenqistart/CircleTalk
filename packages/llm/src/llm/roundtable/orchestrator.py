"""Roundtable orchestration with a deterministic fallback first version."""

from collections.abc import AsyncIterator, Iterable
import logging
from typing import Any, cast

from llm.roundtable.llm_client import RoundtableLLMClient, build_env_roundtable_llm_client
from llm.roundtable.prompts import ROUND_SEQUENCE
from llm.roundtable.schema import (
    DecisionArtifact,
    RoundName,
    RoundtableLanguage,
    RoundtableMessage,
    RoundtableResult,
    RoundtableStreamEvent,
    SelectedPersona,
    normalize_language,
)

logger = logging.getLogger(__name__)


def _persona_line(selected: SelectedPersona, decision_prompt: str, round_name: RoundName, language: RoundtableLanguage = "zh") -> str:
    persona = selected.persona
    if language == "en":
        if round_name == RoundName.OPENING:
            return f'{persona.display_name}: My core judgment is to clarify the goal and unacceptable risks behind "{decision_prompt}" before taking the smallest reversible step.'
        if round_name == RoundName.REBUTTAL:
            return f"{persona.display_name}: I would revise the other views by accounting for {persona.summary}, so the decision threshold includes the strongest opposing risk."
        return f"{persona.display_name}: My revised final judgment is to preserve optionality, run a small validation, and define clear stop conditions."
    if round_name == RoundName.OPENING:
        return f"{persona.display_name}：我的核心判断是先澄清「{decision_prompt}」的目标和不可承受风险，再推进最小可逆行动。"
    if round_name == RoundName.REBUTTAL:
        return f"{persona.display_name}：我回应其他观点：若只看单一视角会遗漏{persona.summary}，因此需要把反方风险纳入决策门槛。"
    return f"{persona.display_name}：修正后的最终判断是保留选择权，先做小规模验证，并设置清晰停止条件。"


def synthesize(
    decision_prompt: str,
    personas: Iterable[SelectedPersona],
    language: RoundtableLanguage | str | None = None,
) -> DecisionArtifact:
    normalized = normalize_language(language)
    persona_list = list(personas)
    debate_map = tuple(
        {
            "persona_id": selected.persona.id,
            "persona_name": selected.persona.display_name,
            "position": f"Constrains this decision from the perspective of {selected.persona.summary}."
            if normalized == "en"
            else f"从{selected.persona.summary}视角约束该决策。",
        }
        for selected in persona_list
    )
    if normalized == "en":
        return DecisionArtifact(
            memo=f'For "{decision_prompt}", the roundtable consensus is not to commit to a single path before clarifying goals, constraints, failure signals, and pilot boundaries.',
            recommendation="Start a short, low-cost, reversible pilot and define continue, pause, and stop thresholds.",
            reasons=("Preserve optionality", "Expose key risks early", "Use real feedback instead of abstract debate"),
            debate_map=debate_map,
        )
    return DecisionArtifact(
        memo=f"围绕“{decision_prompt}”，圆桌共识是不要直接押注单一路径，而是先澄清目标、约束、失败信号与试点边界。",
        recommendation="建议启动一个短周期、低成本、可回滚的试点；同时设定继续、暂停、放弃三个阈值。",
        reasons=("保留选择权", "尽早暴露关键风险", "用真实反馈替代抽象争论"),
        debate_map=debate_map,
    )


class RoundtableOrchestrator:
    """Request-scoped orchestrator; no background jobs or long-term memory."""

    def __init__(self, llm_client: RoundtableLLMClient | None = None) -> None:
        self._llm_client = llm_client if llm_client is not None else build_env_roundtable_llm_client()

    def run(
        self,
        decision_prompt: str,
        personas: list[SelectedPersona],
        language: RoundtableLanguage | str | None = None,
    ) -> RoundtableResult:
        normalized = normalize_language(language)
        messages: list[RoundtableMessage] = []
        for round_name in ROUND_SEQUENCE:
            for selected in personas:
                content = self._generate_persona_message(decision_prompt, selected, round_name, messages, normalized)
                messages.append(
                    RoundtableMessage(
                        role="persona",
                        persona_id=selected.persona.id,
                        persona_name=selected.persona.display_name,
                        round_name=round_name.value,
                        content=content,
                    )
                )
        artifact = self._synthesize(decision_prompt, personas, messages, normalized)
        moderator_content = (
            f"Moderator: {artifact.memo} Recommendation: {artifact.recommendation}"
            if normalized == "en"
            else f"主持人：{artifact.memo} 建议：{artifact.recommendation}"
        )
        messages.append(
            RoundtableMessage(
                role="moderator",
                round_name=RoundName.SYNTHESIS.value,
                content=moderator_content,
            )
        )
        return RoundtableResult(messages=tuple(messages), artifact=artifact)

    async def stream(
        self,
        decision_prompt: str,
        personas: list[SelectedPersona],
        language: RoundtableLanguage | str | None = None,
    ) -> AsyncIterator[RoundtableStreamEvent]:
        normalized = normalize_language(language)
        messages: list[RoundtableMessage] = []
        for round_name in ROUND_SEQUENCE:
            for selected in personas:
                async for event in self._stream_persona_message(decision_prompt, selected, round_name, messages, normalized):
                    if event.message is not None:
                        messages.append(event.message)
                    yield event
        artifact = self._synthesize(decision_prompt, personas, messages, normalized)
        content = (
            f"Moderator: {artifact.memo} Recommendation: {artifact.recommendation}"
            if normalized == "en"
            else f"主持人：{artifact.memo} 建议：{artifact.recommendation}"
        )
        message = RoundtableMessage(
            role="moderator",
            round_name=RoundName.SYNTHESIS.value,
            content=content,
        )
        yield RoundtableStreamEvent(text=f"{message.content}\n\n", message=message, artifact=artifact)

    def _generate_persona_message(
        self,
        decision_prompt: str,
        selected: SelectedPersona,
        round_name: RoundName,
        prior_messages: list[RoundtableMessage],
        language: RoundtableLanguage = "zh",
    ) -> str:
        if self._llm_client is None:
            return _persona_line(selected, decision_prompt, round_name, language)
        try:
            content = self._llm_client.generate_persona_message(
                decision_prompt=decision_prompt,
                selected=selected,
                round_name=round_name,
                prior_messages=prior_messages,
                language=language,
            )
        except Exception:
            logger.exception("roundtable LLM persona generation failed, falling back")
            return _persona_line(selected, decision_prompt, round_name, language)
        return content or _persona_line(selected, decision_prompt, round_name, language)

    async def _stream_persona_message(
        self,
        decision_prompt: str,
        selected: SelectedPersona,
        round_name: RoundName,
        prior_messages: list[RoundtableMessage],
        language: RoundtableLanguage = "zh",
    ) -> AsyncIterator[RoundtableStreamEvent]:
        content = ""
        if self._llm_client is not None:
            stream_method = getattr(cast(Any, self._llm_client), "stream_persona_message", None)
            if stream_method is not None:
                try:
                    async for chunk in stream_method(
                        decision_prompt=decision_prompt,
                        selected=selected,
                        round_name=round_name,
                        prior_messages=prior_messages,
                        language=language,
                    ):
                        content += chunk
                        yield RoundtableStreamEvent(text=chunk)
                except Exception:
                    logger.exception("roundtable LLM persona stream failed, falling back")
                    if content.strip():
                        yield RoundtableStreamEvent(text="\n\n")
                    else:
                        content = _persona_line(selected, decision_prompt, round_name, language)
                        yield RoundtableStreamEvent(text=f"{content}\n\n")
                else:
                    content = content.strip()
                    if content:
                        yield RoundtableStreamEvent(text="\n\n")

        if not content.strip():
            content = self._generate_persona_message(decision_prompt, selected, round_name, prior_messages, language)
            yield RoundtableStreamEvent(text=f"{content}\n\n")

        yield RoundtableStreamEvent(
            message=RoundtableMessage(
                role="persona",
                persona_id=selected.persona.id,
                persona_name=selected.persona.display_name,
                round_name=round_name.value,
                content=content.strip(),
            )
        )

    def _synthesize(
        self,
        decision_prompt: str,
        personas: list[SelectedPersona],
        messages: list[RoundtableMessage],
        language: RoundtableLanguage = "zh",
    ) -> DecisionArtifact:
        if self._llm_client is None:
            return synthesize(decision_prompt, personas, language)
        try:
            return self._llm_client.synthesize(
                decision_prompt=decision_prompt,
                personas=personas,
                messages=messages,
                language=language,
            )
        except Exception:
            logger.exception("roundtable LLM synthesis failed, falling back")
            return synthesize(decision_prompt, personas, language)

    async def follow_up(
        self,
        question: str,
        selected_personas: list[SelectedPersona],
        transcript: list[str],
        artifact: DecisionArtifact | None,
        language: RoundtableLanguage | str | None = None,
    ) -> RoundtableMessage:
        normalized = normalize_language(language)
        if self._llm_client is not None:
            try:
                content = self._llm_client.follow_up(
                    question=question,
                    selected_personas=selected_personas,
                    transcript=transcript,
                    artifact=artifact,
                    language=normalized,
                )
                if content:
                    return RoundtableMessage(
                        role="moderator",
                        round_name=RoundName.FOLLOW_UP.value,
                        content=content,
                    )
            except Exception:
                logger.exception("roundtable LLM follow-up failed, falling back")
        content = _follow_up_line(question, selected_personas, transcript, artifact, normalized)
        return RoundtableMessage(
            role="moderator",
            round_name=RoundName.FOLLOW_UP.value,
            content=content,
        )

    async def stream_follow_up(
        self,
        question: str,
        selected_personas: list[SelectedPersona],
        transcript: list[str],
        artifact: DecisionArtifact | None,
        language: RoundtableLanguage | str | None = None,
    ) -> AsyncIterator[RoundtableStreamEvent]:
        normalized = normalize_language(language)
        content = ""
        if self._llm_client is not None:
            stream_method = getattr(cast(Any, self._llm_client), "stream_follow_up", None)
            if stream_method is not None:
                try:
                    async for chunk in stream_method(
                        question=question,
                        selected_personas=selected_personas,
                        transcript=transcript,
                        artifact=artifact,
                        language=normalized,
                    ):
                        content += chunk
                        yield RoundtableStreamEvent(text=chunk)
                except Exception:
                    logger.exception("roundtable LLM follow-up stream failed, falling back")
                    if content.strip():
                        yield RoundtableStreamEvent(text="\n")
                    else:
                        content = _follow_up_line(question, selected_personas, transcript, artifact, normalized)
                        yield RoundtableStreamEvent(text=f"{content}\n")
                else:
                    content = content.strip()
                    if content:
                        yield RoundtableStreamEvent(text="\n")

        if not content.strip():
            content = _follow_up_line(question, selected_personas, transcript, artifact, normalized)
            yield RoundtableStreamEvent(text=f"{content}\n")

        yield RoundtableStreamEvent(
            message=RoundtableMessage(
                role="moderator",
                round_name=RoundName.FOLLOW_UP.value,
                content=content.strip(),
            )
        )


def _follow_up_line(
    question: str,
    selected_personas: list[SelectedPersona],
    transcript: list[str],
    artifact: DecisionArtifact | None,
    language: RoundtableLanguage = "zh",
) -> str:
    if language == "en":
        names = ", ".join(selected.persona.display_name for selected in selected_personas) or "the current roundtable"
        prior = f"reviewed {len(transcript)} transcript entries"
        recommendation = artifact.recommendation if artifact else "complete the context before acting"
        return f"Follow-up: {question}\nThe moderator integrates {names}; {prior}. Continuing recommendation: {recommendation}."
    names = "、".join(selected.persona.display_name for selected in selected_personas) or "当前圆桌"
    prior = f"已参考 {len(transcript)} 条记录"
    recommendation = artifact.recommendation if artifact else "先补齐上下文后再行动"
    return f"追问：{question}\n主持人综合{names}观点，{prior}。延续建议：{recommendation}。"
