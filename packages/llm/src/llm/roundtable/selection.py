"""Persona selection policy for roundtable sessions."""

from llm.roundtable.schema import RoundtablePersona, SelectedPersona

_KEYWORDS: dict[str, tuple[str, ...]] = {
    "drucker": ("公司", "管理", "组织", "团队", "绩效", "业务", "产品", "创业"),
    "munger": ("投资", "风险", "失败", "激励", "商业", "决策", "成本"),
    "socrates": ("是否", "应该", "选择", "困惑", "问题", "为什么", "价值"),
    "zeng-guofan": ("长期", "职业", "坚持", "转型", "资源", "家庭", "压力"),
    "simone-weil": ("伦理", "人", "教育", "社会", "公平", "员工", "影响"),
}


def _score_persona(persona: RoundtablePersona, decision_prompt: str) -> int:
    text = f"{decision_prompt} {persona.summary}".lower()
    return sum(1 for keyword in _KEYWORDS.get(persona.id, ()) if keyword.lower() in text)


def recommend_personas(
    decision_prompt: str,
    candidates: list[RoundtablePersona],
    *,
    minimum: int = 3,
    maximum: int = 5,
) -> list[SelectedPersona]:
    """Recommend 3-5 diverse personas with reasons when the user did not manually choose."""
    if not decision_prompt.strip():
        msg = "decision_prompt is required"
        raise ValueError(msg)
    if len(candidates) < minimum:
        msg = "not enough persona candidates"
        raise ValueError(msg)
    ranked = sorted(candidates, key=lambda persona: (-_score_persona(persona, decision_prompt), persona.id))
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


def select_manual_personas(persona_ids: list[str], candidates: list[RoundtablePersona]) -> list[SelectedPersona]:
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
