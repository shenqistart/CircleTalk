"""Round policy prompts adapted from zhuzi-skill."""

ROUND_SEQUENCE: tuple[str, str, str] = ("opening", "rebuttal", "closing")

ROUND_PROMPTS: dict[str, str] = {
    "opening": "Opening：给出你的核心判断、关键依据和最担心的风险。",
    "rebuttal": "Rebuttal：必须回应其他人物的观点，指出你同意、反对或补充之处。",
    "closing": "Closing：基于交锋修正你的最终判断，并给出可执行建议。",
}
