"""Roundtable dialogue value objects."""

from dataclasses import dataclass, field
from typing import Literal

RoundName = Literal["opening", "rebuttal", "closing"]


@dataclass(frozen=True)
class RoundtablePersona:
    id: str
    display_name: str
    skill_name: str
    summary: str
    prompt: str
    source_url: str | None = None
    selection_reason: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class PersonaRecommendation:
    persona: RoundtablePersona
    reason: str


@dataclass(frozen=True)
class RoundtableTurn:
    persona_id: str | None
    persona_name: str | None
    role: Literal["user", "persona", "moderator", "system"]
    round_name: RoundName | Literal["synthesis", "follow_up", "system"]
    content: str


@dataclass(frozen=True)
class DecisionArtifact:
    memo: str
    recommendation: str
    reasons: list[str]
    debate_map: list[dict[str, str]]


@dataclass(frozen=True)
class RoundtableResult:
    transcript: list[RoundtableTurn]
    artifact: DecisionArtifact
