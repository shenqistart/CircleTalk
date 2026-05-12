"""Roundtable orchestration with a deterministic fallback first version."""

from collections.abc import Iterable

from llm.roundtable.prompts import ROUND_SEQUENCE
from llm.roundtable.schema import DecisionArtifact, RoundName, RoundtableMessage, RoundtableResult, SelectedPersona


def _persona_line(persona: SelectedPersona, round_name: RoundName, decision_prompt: str) -> str:
    name = persona.persona.display_name
    summary = persona.persona.summary
    match round_name:
        case RoundName.OPENING:
            return f"{name}：我先看目标与不可逆风险。针对“{decision_prompt}”，建议先把成功标准和停止条件写清楚。{summary}"
        case RoundName.REBUTTAL:
            return f"{name}：回应其他观点，我会追问哪些建议只是在转移风险；若要推进，应先做低成本验证。"
        case RoundName.CLOSING:
            return f"{name}：修正后的最终判断是保留选择权，先小步试点，再根据真实反馈扩大投入。"
        case _:
            return f"{name}：继续围绕该问题补充判断。"


def synthesize(decision_prompt: str, selected_personas: Iterable[SelectedPersona]) -> DecisionArtifact:
    """Create the required memo/recommendation/reasons/debate_map artifact."""
    personas = list(selected_personas)
    debate_map = tuple(
        {
            "personaName": persona.persona.display_name,
            "position": "先识别关键假设，再用可逆试点验证。",
            "keyConcern": persona.selection_reason or persona.persona.summary,
        }
        for persona in personas
    )
    return DecisionArtifact(
        memo=f"围绕“{decision_prompt}”，圆桌共识是不要直接押注单一路径，而是先澄清目标、约束、失败信号与试点边界。",
        recommendation="建议启动一个短周期、低成本、可回滚的试点；同时设定继续、暂停、放弃三个阈值。",
        reasons=("保留选择权", "尽早暴露关键风险", "用真实反馈替代抽象争论"),
        debate_map=debate_map,
    )


class RoundtableOrchestrator:
    """Request-scoped orchestrator; no background jobs or long-term memory."""

    async def run(self, decision_prompt: str, selected_personas: list[SelectedPersona]) -> RoundtableResult:
        messages: list[RoundtableMessage] = []
        for round_name in ROUND_SEQUENCE:
            for selected in selected_personas:
                messages.append(
                    RoundtableMessage(
                        role="persona",
                        persona_id=selected.persona.id,
                        persona_name=selected.persona.display_name,
                        round_name=round_name.value,
                        content=_persona_line(selected, round_name, decision_prompt),
                    )
                )
        artifact = synthesize(decision_prompt, selected_personas)
        messages.append(
            RoundtableMessage(
                role="moderator",
                round_name=RoundName.SYNTHESIS.value,
                content=f"主持人：{artifact.memo} 建议：{artifact.recommendation}",
            )
        )
        return RoundtableResult(messages=tuple(messages), artifact=artifact)

    async def follow_up(
        self,
        question: str,
        selected_personas: list[SelectedPersona],
        transcript: list[str],
        artifact: DecisionArtifact | None,
    ) -> RoundtableMessage:
        names = "、".join(selected.persona.display_name for selected in selected_personas)
        prior = f"已参考 {len(transcript)} 条 transcript"
        recommendation = artifact.recommendation if artifact else "先补齐上下文后再行动"
        return RoundtableMessage(
            role="moderator",
            round_name=RoundName.FOLLOW_UP.value,
            content=f"追问：{question}\n主持人综合{names}观点，{prior}。延续建议：{recommendation}。",
        )
