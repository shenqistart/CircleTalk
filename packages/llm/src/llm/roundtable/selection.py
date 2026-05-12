"""Persona recommendation and manual-selection precedence rules."""

from llm.roundtable.persona import get_personas, list_personas
from llm.roundtable.schema import PersonaRecommendation, RoundtablePersona

_KEYWORDS: tuple[tuple[str, str], ...] = (
    ("组织", "drucker"),
    ("管理", "drucker"),
    ("创业", "munger"),
    ("投资", "munger"),
    ("风险", "zeng-guofan"),
    ("长期", "zeng-guofan"),
    ("伦理", "simone-weil"),
    ("人", "simone-weil"),
    ("假设", "socrates"),
    ("选择", "socrates"),
)


def recommend_personas(decision_prompt: str, minimum: int = 3, maximum: int = 5) -> list[PersonaRecommendation]:
    if not decision_prompt.strip():
        msg = "decision prompt is required"
        raise ValueError(msg)

    catalog = {persona.id: persona for persona in list_personas()}
    ordered_ids: list[str] = []
    for keyword, persona_id in _KEYWORDS:
        if keyword in decision_prompt and persona_id not in ordered_ids:
            ordered_ids.append(persona_id)
    for persona in catalog.values():
        if persona.id not in ordered_ids:
            ordered_ids.append(persona.id)
    selected = ordered_ids[: max(minimum, min(maximum, len(ordered_ids)))]
    return [
        PersonaRecommendation(
            persona=catalog[persona_id],
            reason=f"从 {catalog[persona_id].display_name} 的视角补足：{catalog[persona_id].summary}",
        )
        for persona_id in selected
    ]


def select_personas(decision_prompt: str, persona_ids: list[str] | None) -> tuple[list[RoundtablePersona], str, dict[str, str]]:
    if persona_ids:
        personas = get_personas(persona_ids)
        return personas, "manual", {}

    recommendations = recommend_personas(decision_prompt)
    return [item.persona for item in recommendations], "auto", {item.persona.id: item.reason for item in recommendations}
