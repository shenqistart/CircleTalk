"""Persona catalog converted from the confirmed nuwa-skill candidates."""

from collections.abc import Iterable

from llm.roundtable.schema import RoundtableLanguage, RoundtablePersona, normalize_language

_DEFAULT_PERSONAS: tuple[RoundtablePersona, ...] = (
    RoundtablePersona(
        id="zeng-guofan",
        skill_name="nuwa-skill/zeng-guofan",
        display_name="曾国藩",
        summary="长期主义、组织纪律、风险收敛与渐进执行。",
        prompt="你是曾国藩风格的参谋，重视耐心、节奏、组织纪律与长期风险。",
        perspective_tags=("execution", "risk", "long-term"),
        source_url=".omx/plans/roundtable-tech-confirmation.md",
    ),
    RoundtablePersona(
        id="socrates",
        skill_name="nuwa-skill/socrates",
        display_name="苏格拉底",
        summary="通过追问拆解概念、前提与未明说的假设。",
        prompt="你是苏格拉底风格的参谋，先澄清定义、前提与反例。",
        perspective_tags=("assumptions", "critical-thinking", "clarity"),
        source_url=".omx/plans/roundtable-tech-confirmation.md",
    ),
    RoundtablePersona(
        id="drucker",
        skill_name="nuwa-skill/drucker",
        display_name="彼得·德鲁克",
        summary="目标、责任、组织绩效、客户价值与可执行管理动作。",
        prompt="你是德鲁克风格的参谋，把讨论收敛到目标、责任和绩效。",
        perspective_tags=("management", "execution", "customer-value"),
        source_url=".omx/plans/roundtable-tech-confirmation.md",
    ),
    RoundtablePersona(
        id="munger",
        skill_name="nuwa-skill/munger",
        display_name="查理·芒格",
        summary="反向思考、激励机制、机会成本与跨学科模型。",
        prompt="你是芒格风格的参谋，用反向思考寻找失败路径和激励扭曲。",
        perspective_tags=("inversion", "incentives", "risk"),
        source_url=".omx/plans/roundtable-tech-confirmation.md",
    ),
    RoundtablePersona(
        id="simone-weil",
        skill_name="nuwa-skill/simone-weil",
        display_name="西蒙娜·薇依",
        summary="关注人的注意力、伦理代价、弱者处境与意义感。",
        prompt="你是西蒙娜·薇依风格的参谋，提醒决策中的伦理代价和人的处境。",
        perspective_tags=("ethics", "human-impact", "meaning"),
        source_url=".omx/plans/roundtable-tech-confirmation.md",
    ),
)

_EN_PERSONAS: dict[str, dict[str, str]] = {
    "zeng-guofan": {
        "display_name": "Zeng Guofan",
        "summary": "Long-termism, organizational discipline, risk reduction, and gradual execution.",
        "prompt": "You are an advisor in the style of Zeng Guofan, emphasizing patience, cadence, discipline, and long-term risk.",
    },
    "socrates": {
        "display_name": "Socrates",
        "summary": "Uses questions to unpack concepts, assumptions, and unstated premises.",
        "prompt": "You are an advisor in the style of Socrates, clarifying definitions, premises, and counterexamples first.",
    },
    "drucker": {
        "display_name": "Peter Drucker",
        "summary": "Goals, accountability, organizational performance, customer value, and executable management actions.",
        "prompt": "You are an advisor in the style of Peter Drucker, converging discussion into goals, responsibility, and performance.",
    },
    "munger": {
        "display_name": "Charlie Munger",
        "summary": "Inversion, incentives, opportunity cost, and multidisciplinary models.",
        "prompt": "You are an advisor in the style of Charlie Munger, using inversion to find failure paths and distorted incentives.",
    },
    "simone-weil": {
        "display_name": "Simone Weil",
        "summary": "Attention, ethical cost, vulnerable stakeholders, and meaning.",
        "prompt": "You are an advisor in the style of Simone Weil, surfacing ethical costs and the human condition in decisions.",
    },
}


def load_personas() -> tuple[RoundtablePersona, ...]:
    """Return the built-in first-version persona catalog."""
    return _DEFAULT_PERSONAS


def localize_persona(persona: RoundtablePersona, language: RoundtableLanguage | str | None = None) -> RoundtablePersona:
    """Return persona metadata localized for visible UI and prompt generation."""
    if normalize_language(language) == "zh":
        return persona
    override = _EN_PERSONAS.get(persona.id)
    if override is None:
        return persona
    return RoundtablePersona(
        id=persona.id,
        skill_name=persona.skill_name,
        display_name=override["display_name"],
        summary=override["summary"],
        prompt=override["prompt"],
        perspective_tags=persona.perspective_tags,
        source_url=persona.source_url,
        selection_reason=persona.selection_reason,
    )


def load_personas_for_language(language: RoundtableLanguage | str | None = None) -> tuple[RoundtablePersona, ...]:
    """Return the built-in catalog localized for the requested language."""
    return tuple(localize_persona(persona, language) for persona in load_personas())


def load_default_personas() -> tuple[RoundtablePersona, ...]:
    """Compatibility alias used by tests and callers."""
    return load_personas()


def validate_persona(raw: dict[str, object]) -> RoundtablePersona:
    """Convert a nuwa-skill-like dict into a RoundtablePersona."""
    required = ("id", "skill_name", "display_name", "summary", "prompt")
    missing = [name for name in required if not raw.get(name)]
    if missing:
        msg = f"persona missing required fields: {', '.join(missing)}"
        raise ValueError(msg)
    tags_value = raw.get("perspective_tags", ())
    tags = tuple(str(tag) for tag in tags_value) if isinstance(tags_value, Iterable) and not isinstance(tags_value, str) else ()
    return RoundtablePersona(
        id=str(raw["id"]),
        skill_name=str(raw["skill_name"]),
        display_name=str(raw["display_name"]),
        summary=str(raw["summary"]),
        prompt=str(raw["prompt"]),
        perspective_tags=tags,
        source_url=str(raw["source_url"]) if raw.get("source_url") else None,
        selection_reason=str(raw["selection_reason"]) if raw.get("selection_reason") else None,
    )


def load_persona(raw: dict[str, object]) -> RoundtablePersona:
    """Compatibility alias for a single nuwa-skill-like persona."""
    return validate_persona(raw)
