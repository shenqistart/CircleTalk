"""Persona recommendation and manual-selection precedence."""

from llm.roundtable.persona import load_personas_for_language
from llm.roundtable.schema import RoundtableLanguage, RoundtablePersona, SelectedPersona, normalize_language

_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("drucker", ("管理", "组织", "团队", "业务", "客户", "绩效", "创业")),
    ("munger", ("投资", "风险", "失败", "激励", "机会成本", "决策")),
    ("socrates", ("是否", "应该", "选择", "困惑", "假设", "定义")),
    ("zeng-guofan", ("长期", "执行", "坚持", "转型", "战略", "复杂")),
    ("simone-weil", ("伦理", "人", "意义", "公平", "痛苦", "关系")),
)


def _reason_for(persona: RoundtablePersona, decision_prompt: str, language: RoundtableLanguage) -> str:
    prompt = decision_prompt[:24]
    if language == "en":
        return f'Complements the perspective needed for "{prompt}" and contributes {persona.summary}'
    return f"与「{prompt}」的问题视角互补，可提供{persona.summary}"


def recommend_personas(
    decision_prompt: str,
    personas: tuple[RoundtablePersona, ...] | None = None,
    language: RoundtableLanguage | str | None = None,
) -> list[SelectedPersona]:
    """Recommend 3-5 diverse personas for an unassigned decision prompt."""
    normalized = normalize_language(language)
    prompt = decision_prompt.strip()
    if not prompt:
        msg = "decision prompt is required"
        raise ValueError(msg)

    catalog = list(personas or load_personas_for_language(normalized))
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
        selected.extend(persona for persona in catalog if persona not in selected)

    return [
        SelectedPersona(
            persona=persona,
            selection_source="auto",
            sequence=index + 1,
            selection_reason=_reason_for(persona, prompt, normalized),
        )
        for index, persona in enumerate(selected[:5])
    ]


def select_manual_personas(
    persona_ids: list[str],
    personas: tuple[RoundtablePersona, ...] | None = None,
    language: RoundtableLanguage | str | None = None,
) -> list[SelectedPersona]:
    """Preserve explicit user selection and never override it with auto recommendation."""
    if not persona_ids:
        msg = "manual persona_ids must not be empty"
        raise ValueError(msg)
    normalized = normalize_language(language)
    catalog = personas or load_personas_for_language(normalized)
    by_id = {persona.id: persona for persona in catalog}
    unknown = [persona_id for persona_id in persona_ids if persona_id not in by_id]
    if unknown:
        msg = f"unknown persona_ids: {', '.join(unknown)}"
        raise ValueError(msg)
    return [
        SelectedPersona(
            persona=by_id[persona_id],
            selection_source="manual",
            selection_reason="Explicitly selected by the user; takes precedence over automatic recommendation."
            if normalized == "en"
            else "用户显式选择，优先于自动推荐。",
            sequence=index + 1,
        )
        for index, persona_id in enumerate(persona_ids)
    ]


def select_personas(
    decision_prompt: str,
    persona_ids: list[str] | None = None,
    language: RoundtableLanguage | str | None = None,
) -> list[SelectedPersona]:
    """Use explicit manual choices when present; otherwise auto-recommend."""
    if persona_ids:
        return select_manual_personas(persona_ids, language=language)
    return recommend_personas(decision_prompt, language=language)
