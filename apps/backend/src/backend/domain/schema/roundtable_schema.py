"""Roundtable API schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


def to_camel(value: str) -> str:
    parts = value.split("_")
    return parts[0] + "".join(part.title() for part in parts[1:])


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class RoundtablePersonaSchema(CamelModel):
    id: str
    display_name: str
    skill_name: str
    summary: str
    selection_reason: str | None = None


class SelectedPersonaSchema(RoundtablePersonaSchema):
    selection_source: Literal["auto", "manual"]
    sequence: int


class RoundtableMessageSchema(CamelModel):
    id: str
    role: Literal["moderator", "persona", "user", "system"]
    content: str
    round_name: str
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
    status: str
    selected_personas: list[SelectedPersonaSchema]
    transcript: list[RoundtableMessageSchema]
    artifacts: DecisionArtifactSchema | None = None
    created_at: datetime
    updated_at: datetime


class CreateRoundtableSessionRequest(CamelModel):
    decision_prompt: str = Field(min_length=1, max_length=4000)
    persona_ids: list[str] | None = Field(default=None, min_length=1)


class CreateRoundtableSessionResponse(CamelModel):
    session: RoundtableSessionSchema
    recommended_personas: list[RoundtablePersonaSchema]


class RecommendPersonasRequest(CamelModel):
    decision_prompt: str = Field(min_length=1, max_length=4000)


class FollowUpRequest(CamelModel):
    question: str = Field(min_length=1, max_length=4000)
