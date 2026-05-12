from llm.roundtable import (
    load_default_personas,
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


def test_round_policy_and_adapter_fallback() -> None:
    assert ROUND_SEQUENCE == ("opening", "rebuttal", "closing")
    assert "回应" in ROUND_PROMPTS["rebuttal"]
    assert "修正" in ROUND_PROMPTS["closing"]
    personas = recommend_personas("如何评估一次职业转型", load_default_personas())
    result = RoundtableDeepAgentAdapter().run("如何评估一次职业转型", personas)
    assert {message.round_name for message in result.messages} >= {
        "opening",
        "rebuttal",
        "closing",
        "synthesis",
    }
    assert result.artifact.memo
