"""Roundtable request/response schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

type RoundtableSessionStatus = Literal["draft", "ready", "streaming", "completed", "error", "cancelled"]
type PersonaSelectionSource = Literal["auto", "manual"]
type RoundtableMessageRole = Literal["moderator", "persona", "user", "system"]
type RoundtableRoundName = Literal["opening", "rebuttal", "closing", "synthesis", "follow_up", "system"]


def to_camel(value: str) -> str:
    head, *tail = value.split("_")
    return head + "".join(part.capitalize() for part in tail)


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class RoundtablePersonaSchema(CamelModel):
    id: str
    display_name: str
    skill_name: str
    summary: str
    selection_reason: str | None = None


class SelectedPersonaSchema(RoundtablePersonaSchema):
    selection_source: PersonaSelectionSource
    sequence: int


class RoundtableMessageSchema(CamelModel):
    id: str
    role: RoundtableMessageRole
    content: str
    round_name: RoundtableRoundName
    sequence: int
    created_at: datetime
    persona_id: str | None = None
    persona_name: str | None = None


class DecisionArtifactSchema(CamelModel):
    memo: str
    recommendation: str
    reasons: list[str]
    debate_map: list[dict[str, str]]


class RoundtableSessionSchema(CamelModel):
    id: str
    decision_prompt: str
    status: RoundtableSessionStatus
    selected_personas: list[SelectedPersonaSchema]
    transcript: list[RoundtableMessageSchema]
    artifacts: DecisionArtifactSchema | None = None
    created_at: datetime
    updated_at: datetime


class CreateRoundtableSessionRequest(CamelModel):
    decision_prompt: str = Field(min_length=1, max_length=4000)
    persona_ids: list[str] = Field(default_factory=list)


class CreateRoundtableSessionResponse(CamelModel):
    session: RoundtableSessionSchema
    recommended_personas: list[RoundtablePersonaSchema]


class RecommendPersonasRequest(CamelModel):
    decision_prompt: str = Field(min_length=1, max_length=4000)


class FollowUpRequest(CamelModel):
    question: str = Field(min_length=1, max_length=4000)
