"""Synchronous first-version roundtable orchestrator."""

from collections.abc import Iterable

from llm.roundtable.prompts import ROUND_PROMPTS, ROUND_SEQUENCE
from llm.roundtable.schema import DecisionArtifact, RoundtablePersona, RoundtableResult, RoundtableTurn


def _persona_line(persona: RoundtablePersona, decision_prompt: str, round_name: str) -> str:
    if round_name == "opening":
        return f"{persona.display_name}：我的核心判断是先把‘{decision_prompt}’拆成目标、约束和风险，再做小步验证。{ROUND_PROMPTS[round_name]}"
    if round_name == "rebuttal":
        return f"{persona.display_name}：我回应其他观点：若只看单一收益会低估代价，需要用我的视角校正。{ROUND_PROMPTS[round_name]}"
    return f"{persona.display_name}：修正后的最终判断是保留选择权，设定可逆试点和停止条件。{ROUND_PROMPTS[round_name]}"


def synthesize(decision_prompt: str, personas: Iterable[RoundtablePersona]) -> DecisionArtifact:
    persona_list = list(personas)
    debate_map = [
        {
            "personaName": persona.display_name,
            "position": "先做可逆试点，再依据证据扩大投入。",
            "keyConcern": persona.summary,
        }
        for persona in persona_list
    ]
    return DecisionArtifact(
        memo=f"围绕“{decision_prompt}”，圆桌一致建议先澄清目标、约束、失败条件和最小验证路径。",
        recommendation="推进一个低成本、可回滚的短周期试点；若关键指标未达标则停止或调整。",
        reasons=["保留选择权", "用真实反馈替代抽象争论", "提前暴露组织、伦理与激励风险"],
        debate_map=debate_map,
    )


def run_roundtable(decision_prompt: str, personas: list[RoundtablePersona]) -> RoundtableResult:
    if not personas:
        msg = "at least one persona is required"
        raise ValueError(msg)
    transcript: list[RoundtableTurn] = [
        RoundtableTurn(
            persona_id=None,
            persona_name=None,
            role="user",
            round_name="system",
            content=decision_prompt,
        )
    ]
    for round_name in ROUND_SEQUENCE:
        for persona in personas:
            transcript.append(
                RoundtableTurn(
                    persona_id=persona.id,
                    persona_name=persona.display_name,
                    role="persona",
                    round_name=round_name,
                    content=_persona_line(persona, decision_prompt, round_name),
                )
            )
    artifact = synthesize(decision_prompt, personas)
    transcript.append(
        RoundtableTurn(
            persona_id=None,
            persona_name=None,
            role="moderator",
            round_name="synthesis",
            content=f"主持人：{artifact.recommendation}",
        )
    )
    return RoundtableResult(transcript=transcript, artifact=artifact)


def answer_follow_up(question: str, personas: list[RoundtablePersona], previous_recommendation: str | None) -> RoundtableTurn:
    names = "、".join(persona.display_name for persona in personas)
    base = previous_recommendation or "先恢复既有 transcript 与三件套，再补充回答。"
    return RoundtableTurn(
        persona_id=None,
        persona_name=None,
        role="moderator",
        round_name="follow_up",
        content=f"追问：{question}\n基于 {names} 的既有圆桌与结论，延伸建议：{base}",
    )
