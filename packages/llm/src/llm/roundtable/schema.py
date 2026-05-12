"""Roundtable decision advisor domain schemas."""

from dataclasses import dataclass, field
from enum import StrEnum


class RoundName(StrEnum):
    """Supported zhuzi-style discussion rounds."""

    OPENING = "opening"
    REBUTTAL = "rebuttal"
    CLOSING = "closing"
    SYNTHESIS = "synthesis"
    FOLLOW_UP = "follow_up"


@dataclass(frozen=True)
class RoundtablePersona:
    """Persona metadata converted from nuwa-skill style sources."""

    id: str
    skill_name: str
    display_name: str
    summary: str
    prompt: str
    perspective_tags: tuple[str, ...] = field(default_factory=tuple)
    source_url: str | None = None
    selection_reason: str | None = None


@dataclass(frozen=True)
class SelectedPersona:
    """Persona selected for a session."""

    persona: RoundtablePersona
    selection_source: str
    sequence: int
    selection_reason: str | None = None


@dataclass(frozen=True)
class RoundtableMessage:
    """One persisted roundtable utterance."""

    role: str
    content: str
    round_name: str
    persona_id: str | None = None
    persona_name: str | None = None


@dataclass(frozen=True)
class DecisionArtifact:
    """Moderator synthesis artifact: memo, recommendation, reasons and debate map."""

    memo: str
    recommendation: str
    reasons: tuple[str, ...]
    debate_map: tuple[dict[str, str], ...]


@dataclass(frozen=True)
class RoundtableResult:
    """Completed discussion result."""

    messages: tuple[RoundtableMessage, ...]
    artifact: DecisionArtifact
