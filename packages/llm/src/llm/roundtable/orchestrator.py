"""Roundtable orchestration with a deterministic fallback first version."""

from collections.abc import Iterable

from llm.roundtable.prompts import ROUND_SEQUENCE
from llm.roundtable.schema import (
    DecisionArtifact,
    RoundtableMessage,
    RoundtableRunResult,
    SelectedPersona,
)


def _persona_line(
    persona: SelectedPersona, decision_prompt: str, round_name: str
) -> str:
    if round_name == "opening":
        return f"{persona.display_name}：我的核心判断是先澄清「{decision_prompt}」的目标和不可承受风险，再推进最小可逆行动。"
    if round_name == "rebuttal":
        return f"{persona.display_name}：我回应其他观点：若只看单一视角会遗漏{persona.summary}，因此需要把反方风险纳入决策门槛。"
    return f"{persona.display_name}：修正后的最终判断是保留选择权，先做小规模验证，并设置清晰停止条件。"


def synthesize(
    decision_prompt: str, personas: Iterable[SelectedPersona]
) -> DecisionArtifact:
    persona_list = list(personas)
    return DecisionArtifact(
        memo=f"围绕“{decision_prompt}”，圆桌共识是不要直接押注单一路径，而是先澄清目标、约束、失败信号与试点边界。",
        recommendation="建议启动一个短周期、低成本、可回滚的试点；同时设定继续、暂停、放弃三个阈值。",
        reasons=("保留选择权", "尽早暴露关键风险", "用真实反馈替代抽象争论"),
        debate_map=debate_map,
    )


class RoundtableOrchestrator:
    """Request-scoped orchestrator; no background jobs or long-term memory."""

    def run(
        self, decision_prompt: str, personas: list[SelectedPersona]
    ) -> RoundtableRunResult:
        messages: list[RoundtableMessage] = [
            RoundtableMessage(
                role="user", content=decision_prompt, round_name="system"
            ),
        ]
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
