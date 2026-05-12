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


def _score_persona(persona: RoundtablePersona, decision_prompt: str) -> int:
    text = f"{decision_prompt} {persona.summary}".lower()
    return sum(
        1 for keyword in _KEYWORDS.get(persona.id, ()) if keyword.lower() in text
    )


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
    """Recommend 3-5 diverse personas with reasons when the user did not manually choose."""
    if not decision_prompt.strip():
        msg = "decision_prompt is required"
        raise ValueError(msg)
    if len(candidates) < minimum:
        msg = "not enough persona candidates"
        raise ValueError(msg)
    ranked = sorted(
        candidates,
        key=lambda persona: (-_score_persona(persona, decision_prompt), persona.id),
    )
    count = min(maximum, max(minimum, min(len(candidates), 4)))
    selected = ranked[:count]
    return [
        SelectedPersona(
            **persona.model_dump(exclude={"selection_reason"}),
            selection_source="auto",
            selection_reason=f"与「{decision_prompt[:24]}」的问题视角互补，可提供{persona.summary}",
            sequence=index + 1,
        )
        for index, persona in enumerate(selected)
    ]


def select_manual_personas(
    persona_ids: list[str], candidates: list[RoundtablePersona]
) -> list[SelectedPersona]:
    """Preserve explicit user selection and never override it with auto recommendation."""
    if not persona_ids:
        msg = "manual persona_ids must not be empty"
        raise ValueError(msg)
    by_id = {persona.id: persona for persona in candidates}
    unknown = [persona_id for persona_id in persona_ids if persona_id not in by_id]
    if unknown:
        msg = f"unknown persona_ids: {', '.join(unknown)}"
        raise ValueError(msg)
    return [
        SelectedPersona(
            **by_id[persona_id].model_dump(exclude={"selection_reason"}),
            selection_source="manual",
            selection_reason="用户显式选择，优先于自动推荐。",
            sequence=index + 1,
        )
        for index, persona_id in enumerate(persona_ids)
    ]
