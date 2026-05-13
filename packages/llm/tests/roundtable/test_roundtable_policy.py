import asyncio

from llm.roundtable import (
    DecisionArtifact,
    RoundName,
    RoundtableMessage,
    RoundtableOrchestrator,
    load_default_personas,
    load_personas_for_language,
    load_persona,
    recommend_personas,
    select_manual_personas,
)
from llm.roundtable.prompts import ROUND_PROMPTS, ROUND_SEQUENCE
from llm.roundtable.deep_agent_adapter import RoundtableDeepAgentAdapter


def test_persona_loading_requires_fields() -> None:
    personas = load_default_personas()
    assert personas[0].display_name
    try:
        load_persona({"id": "broken"})
    except ValueError as exc:
        assert "missing required" in str(exc)
    else:
        raise AssertionError("expected missing field error")


def test_auto_recommend_returns_three_to_five_with_reasons() -> None:
    selected = recommend_personas(
        "我是否应该离开大厂做 AI 创业", load_default_personas()
    )
    assert 3 <= len(selected) <= 5
    assert all(persona.selection_source == "auto" for persona in selected)
    assert all(persona.selection_reason for persona in selected)


def test_manual_selection_is_preserved_and_not_overridden() -> None:
    candidates = load_default_personas()
    selected = select_manual_personas(["socrates"], candidates)
    assert [persona.id for persona in selected] == ["socrates"]
    assert selected[0].selection_source == "manual"
    all_selected = select_manual_personas(
        [persona.id for persona in candidates], candidates
    )
    assert len(all_selected) == len(candidates)


def test_english_language_localizes_personas_and_fallback() -> None:
    personas = recommend_personas("Should I build an AI product?", language="en")
    assert personas[0].persona.display_name
    assert all("与" not in (persona.selection_reason or "") for persona in personas)
    result = RoundtableOrchestrator().run("Should I build an AI product?", personas[:1], language="en")
    assert "Moderator:" in result.messages[-1].content
    assert "Start a short" in result.artifact.recommendation
    assert load_personas_for_language("en")[0].display_name == "Zeng Guofan"


def test_round_policy_and_adapter_fallback() -> None:
    assert ROUND_SEQUENCE == ("opening", "rebuttal", "closing")
    assert "回应" in ROUND_PROMPTS[RoundName.REBUTTAL]
    assert "修正" in ROUND_PROMPTS[RoundName.CLOSING]
    personas = recommend_personas("如何评估一次职业转型", load_default_personas())
    result = RoundtableDeepAgentAdapter().run("如何评估一次职业转型", personas)
    assert {message.round_name for message in result.messages} >= {
        "opening",
        "rebuttal",
        "closing",
        "synthesis",
    }
    assert result.artifact.memo


class StubRoundtableLLMClient:
    def generate_persona_message(self, *, decision_prompt, selected, round_name, prior_messages, language="zh"):  # noqa: ANN001
        return f"{selected.persona.display_name}-{round_name.value}-{len(prior_messages)}"

    async def stream_persona_message(self, *, decision_prompt, selected, round_name, prior_messages, language="zh"):  # noqa: ANN001
        yield f"{selected.persona.display_name}-"
        yield f"{round_name.value}-"
        yield str(len(prior_messages))

    def synthesize(self, *, decision_prompt, personas, messages, language="zh"):  # noqa: ANN001
        return DecisionArtifact(
            memo=f"LLM memo: {decision_prompt}",
            recommendation=f"LLM recommendation from {len(messages)} messages",
            reasons=("LLM reason",),
            debate_map=tuple(
                {
                    "persona_name": selected.persona.display_name,
                    "position": "LLM position",
                    "key_concern": "LLM concern",
                }
                for selected in personas
            ),
        )

    def follow_up(self, *, question, selected_personas, transcript, artifact, language="zh"):  # noqa: ANN001
        return f"LLM follow-up: {question} / {len(transcript)}"

    async def stream_follow_up(self, *, question, selected_personas, transcript, artifact, language="zh"):  # noqa: ANN001
        yield "LLM "
        yield f"follow-up: {question} / {len(transcript)}"


class BrokenRoundtableLLMClient:
    def generate_persona_message(self, **kwargs):  # noqa: ANN003
        raise RuntimeError("boom")

    async def stream_persona_message(self, **kwargs):  # noqa: ANN003
        raise RuntimeError("boom")
        yield ""

    def synthesize(self, **kwargs):  # noqa: ANN003
        raise RuntimeError("boom")

    def follow_up(self, **kwargs):  # noqa: ANN003
        raise RuntimeError("boom")

    async def stream_follow_up(self, **kwargs):  # noqa: ANN003
        raise RuntimeError("boom")
        yield ""


def test_orchestrator_uses_llm_client_when_available() -> None:
    personas = select_manual_personas(["socrates", "munger"], load_default_personas())
    result = RoundtableOrchestrator(llm_client=StubRoundtableLLMClient()).run("是否做 AI 产品", personas)
    first = result.messages[0]
    assert first.content == "苏格拉底-opening-0"
    assert result.artifact.memo == "LLM memo: 是否做 AI 产品"
    assert result.artifact.recommendation == "LLM recommendation from 6 messages"


def test_orchestrator_streams_before_synthesis() -> None:
    async def collect() -> list[str]:
        personas = select_manual_personas(["socrates"], load_default_personas())
        events = []
        async for event in RoundtableOrchestrator(llm_client=StubRoundtableLLMClient()).stream("是否做 AI 产品", personas):
            if event.text:
                events.append(event.text)
        return events

    events = asyncio.run(collect())
    assert events[:3] == ["苏格拉底-", "opening-", "0"]
    assert any("主持人：" in event for event in events)


def test_orchestrator_falls_back_when_llm_client_fails() -> None:
    personas = select_manual_personas(["socrates"], load_default_personas())
    orchestrator = RoundtableOrchestrator(llm_client=BrokenRoundtableLLMClient())
    result = orchestrator.run("是否做 AI 产品", personas)
    assert "我的核心判断是先澄清" in result.messages[0].content
    follow_up = asyncio.run(
        orchestrator.follow_up(
            "下一步？",
            personas,
            [message.content for message in result.messages],
            result.artifact,
        )
    )
    assert isinstance(follow_up, RoundtableMessage)
    assert "主持人综合" in follow_up.content
