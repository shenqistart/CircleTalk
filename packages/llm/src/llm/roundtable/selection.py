"""Persona recommendation and manual-selection precedence."""

from llm.roundtable.persona import get_personas_by_ids, load_personas
from llm.roundtable.schema import RoundtablePersona, SelectedPersona

_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("drucker", ("管理", "组织", "团队", "业务", "客户", "绩效", "创业")),
    ("munger", ("投资", "风险", "失败", "激励", "机会成本", "决策")),
    ("socrates", ("是否", "应该", "选择", "困惑", "假设", "定义")),
    ("zeng-guofan", ("长期", "执行", "坚持", "转型", "战略", "复杂")),
    ("simone-weil", ("伦理", "人", "意义", "公平", "痛苦", "关系")),
)


def _reason_for(persona: RoundtablePersona, prompt: str) -> str:
    matched = [word for persona_id, words in _KEYWORDS if persona_id == persona.id for word in words if word in prompt]
    if matched:
        return f"问题包含“{matched[0]}”，适合由{persona.display_name}补足{persona.summary}"
    return f"补足{persona.summary}视角，避免圆桌观点单一。"


def recommend_personas(decision_prompt: str, *, personas: tuple[RoundtablePersona, ...] | None = None) -> list[SelectedPersona]:
    """Recommend 3-5 diverse personas for an unassigned decision prompt."""
    prompt = decision_prompt.strip()
    if not prompt:
        msg = "decision prompt is required"
        raise ValueError(msg)

    catalog = list(personas or load_personas())
    score_by_id = {persona.id: 0 for persona in catalog}
    for persona_id, words in _KEYWORDS:
        score_by_id[persona_id] = sum(2 for word in words if word in prompt)

    ranked = sorted(catalog, key=lambda persona: (-score_by_id[persona.id], persona.id))
    selected: list[RoundtablePersona] = []
    used_tags: set[str] = set()
    for persona in ranked:
        if len(selected) >= 5:
            break
        tags = set(persona.perspective_tags)
        if len(selected) < 3 or not tags.issubset(used_tags):
            selected.append(persona)
            used_tags.update(tags)
    if len(selected) < 3:
        selected.extend(persona for persona in catalog if persona not in selected)  # pragma: no cover
    return [
        SelectedPersona(persona=persona, selection_source="auto", sequence=index + 1, selection_reason=_reason_for(persona, prompt))
        for index, persona in enumerate(selected[:5])
    ]


def select_personas(
    decision_prompt: str,
    persona_ids: list[str] | None,
    *,
    personas: tuple[RoundtablePersona, ...] | None = None,
) -> list[SelectedPersona]:
    """Select manual personas when supplied; otherwise auto-recommend."""
    if persona_ids:
        resolved = get_personas_by_ids(persona_ids, personas)
        return [
            SelectedPersona(persona=persona, selection_source="manual", sequence=index + 1)
            for index, persona in enumerate(resolved)
        ]
    return recommend_personas(decision_prompt, personas=personas)
