"""Round policy prompts inspired by zhuzi-skill."""

ROUND_SEQUENCE = ("opening", "rebuttal", "closing")

ROUND_PROMPTS = {
    "opening": "Opening：给出你的核心判断、最重要依据和一个不可忽略的风险。",
    "rebuttal": "Rebuttal：回应其他人物的观点，指出你同意、反对或需要修正的地方。",
    "closing": "Closing：基于反驳轮修正你的最终判断，给出可执行建议。",
}

SYNTHESIS_PROMPT = "主持人综合：输出备忘录 memo、recommendation、reasons 与 debate_map 三件套。"
