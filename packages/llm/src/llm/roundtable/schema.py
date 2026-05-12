"""Roundtable dialogue domain schemas."""

from pydantic import BaseModel, Field


class RoundtablePersona(BaseModel):
    """A decision persona converted from nuwa-skill metadata."""

    id: str = Field(min_length=1)
    skill_name: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    prompt: str = Field(min_length=1)
    source_url: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)
    selection_reason: str | None = None


class SelectedPersona(RoundtablePersona):
    """A persona selected for one session."""

    selection_source: str
    sequence: int


class RoundtableMessage(BaseModel):
    """One persisted roundtable transcript message."""

    role: str
    content: str
    round_name: str
    persona_id: str | None = None
    persona_name: str | None = None
    parent_message_id: str | None = None


class DecisionArtifact(BaseModel):
    """Moderator synthesis artifacts."""

    memo: str
    recommendation: str
    reasons: list[str]
    debate_map: list[dict[str, str]]


class RoundtableRunResult(BaseModel):
    """Complete deterministic/fallback orchestration result."""

    messages: list[RoundtableMessage]
    artifact: DecisionArtifact
