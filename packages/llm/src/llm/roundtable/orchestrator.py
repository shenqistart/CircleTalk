"""Request-scoped roundtable orchestration."""

from collections.abc import Iterable

from llm.roundtable.prompts import ROUND_SEQUENCE
from llm.roundtable.schema import DecisionArtifact, RoundtableMessage, RoundtableRunResult, SelectedPersona


def _persona_line(persona: SelectedPersona, decision_prompt: str, round_name: str) -> str:
    if round_name == "opening":
        return f"{persona.display_name}：我的核心判断是先澄清「{decision_prompt}」的目标和不可承受风险，再推进最小可逆行动。"
    if round_name == "rebuttal":
        return f"{persona.display_name}：我回应其他观点：若只看单一视角会遗漏{persona.summary}，因此需要把反方风险纳入决策门槛。"
    return f"{persona.display_name}：修正后的最终判断是保留选择权，先做小规模验证，并设置清晰停止条件。"


def synthesize(decision_prompt: str, personas: Iterable[SelectedPersona]) -> DecisionArtifact:
    persona_list = list(personas)
    return DecisionArtifact(
        memo=f"围绕「{decision_prompt}」，圆桌建议用低风险实验验证关键假设，再扩大投入。",
        recommendation="推进一个短周期试点；若关键指标或风险门槛未达标，则暂停或调整方向。",
        reasons=["保留选择权", "尽早暴露关键风险", "用多视角避免单点误判"],
        debate_map=[
            {
                "personaName": persona.display_name,
                "position": "支持先验证再承诺。",
                "keyConcern": persona.selection_reason or persona.summary,
            }
            for persona in persona_list
        ],
    )


class RoundtableOrchestrator:
    """Synchronous first-version orchestrator; DeepAgents adapter can delegate to it as fallback."""

    def run(self, decision_prompt: str, personas: list[SelectedPersona]) -> RoundtableRunResult:
        messages: list[RoundtableMessage] = [
            RoundtableMessage(role="user", content=decision_prompt, round_name="system"),
        ]
        for round_name in ROUND_SEQUENCE:
            for persona in personas:
                messages.append(
                    RoundtableMessage(
                        role="persona",
                        persona_id=persona.id,
                        persona_name=persona.display_name,
                        round_name=round_name,
                        content=_persona_line(persona, decision_prompt, round_name),
                    )
                )
        artifact = synthesize(decision_prompt, personas)
        messages.append(
            RoundtableMessage(
                role="moderator",
                round_name="synthesis",
                content=f"主持人：三件套已生成。建议：{artifact.recommendation}",
            )
        )
        return RoundtableRunResult(messages=messages, artifact=artifact)

    def follow_up(
        self,
        question: str,
        personas: list[SelectedPersona],
        transcript: list[str],
        artifact: DecisionArtifact | None,
    ) -> RoundtableMessage:
        context_size = len(transcript)
        recommendation = artifact.recommendation if artifact else "先补齐三件套后再推进"
        names = "、".join(persona.display_name for persona in personas)
        return RoundtableMessage(
            role="moderator",
            round_name="follow_up",
            content=f"基于已有 {context_size} 条 transcript 和 {names} 的视角，回应追问「{question}」：延续建议——{recommendation}。",
        )
