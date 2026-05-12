"""Zhuzi-style round policy prompts."""

from llm.roundtable.schema import RoundName

ROUND_SEQUENCE: tuple[RoundName, ...] = (RoundName.OPENING, RoundName.REBUTTAL, RoundName.CLOSING)

ROUND_PROMPTS: dict[RoundName, str] = {
    RoundName.OPENING: "给出你对该决策题的核心判断，明确最重要的目标、约束和风险。",
    RoundName.REBUTTAL: "回应其他人物的观点，指出你同意、反对或需要修正之处，不要只重复自己的 opening。",
    RoundName.CLOSING: "基于前两轮争论给出修正后的最终判断，说明保留意见与行动建议。",
}

SYNTHESIS_PROMPT = "主持人汇总 memo、recommendation、reasons 和 debate_map 三件套。"
