"""Versioned Roundtable worker request, response, and stream schemas."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.domain.schema.roundtable_schema import RoundtableLanguage, to_camel

WORKER_CONTRACT_VERSION = "roundtable.worker.v1"

type WorkerContractVersion = Literal["roundtable.worker.v1"]
type WorkerStreamEventType = Literal[
    "roundtable.worker.v1.started",
    "roundtable.worker.v1.message.delta",
    "roundtable.worker.v1.message.completed",
    "roundtable.worker.v1.artifact.updated",
    "roundtable.worker.v1.completed",
    "roundtable.worker.v1.error",
]


class WorkerCamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class WorkerPersona(WorkerCamelModel):
    id: str
    name: str
    title: str
    description: str
    expertise: list[str] = Field(default_factory=list)
    language: RoundtableLanguage = "zh"
    avatar_url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkerSelectedPersona(WorkerPersona):
    selection_source: Literal["auto", "manual"] = "manual"
    selection_reason: str | None = None
    sequence: int = Field(ge=1)


class WorkerMessage(WorkerCamelModel):
    role: Literal["moderator", "persona", "user", "system"]
    content: str = Field(min_length=1)
    round_name: Literal["opening", "rebuttal", "closing", "synthesis", "follow_up", "system"] = "system"
    persona_id: str | None = None
    persona_name: str | None = None
    sequence: int = Field(default=1, ge=1)


class WorkerArtifact(WorkerCamelModel):
    memo: str
    recommendation: str
    reasons: list[str] = Field(default_factory=list)
    debate_map: list[dict[str, str]] = Field(default_factory=list)


class WorkerBaseRequest(WorkerCamelModel):
    contract_version: str = WORKER_CONTRACT_VERSION
    request_id: str = Field(min_length=1)


class RecommendPersonasRequestV1(WorkerBaseRequest):
    decision_prompt: str = Field(min_length=1, max_length=4000)
    language: RoundtableLanguage = "zh"
    max_personas: int = Field(default=3, ge=1, le=12)
    context: dict[str, Any] | None = None


class RecommendPersonasResponseV1(WorkerCamelModel):
    contract_version: WorkerContractVersion = WORKER_CONTRACT_VERSION
    request_id: str
    personas: list[WorkerPersona]


class StartDiscussionRequestV1(WorkerBaseRequest):
    session_id: str = Field(min_length=1)
    user_id_hash: str = Field(min_length=1)
    decision_prompt: str = Field(min_length=1, max_length=4000)
    language: RoundtableLanguage = "zh"
    personas: list[WorkerSelectedPersona] = Field(min_length=1)
    prior_messages: list[WorkerMessage] = Field(default_factory=list)
    artifact: WorkerArtifact | None = None


class FollowUpRequestV1(WorkerBaseRequest):
    session_id: str = Field(min_length=1)
    user_id_hash: str = Field(min_length=1)
    question: str = Field(min_length=1, max_length=4000)
    language: RoundtableLanguage = "zh"
    personas: list[WorkerSelectedPersona] = Field(min_length=1)
    messages: list[WorkerMessage] = Field(default_factory=list)
    artifact: WorkerArtifact | None = None


class WorkerErrorV1(WorkerCamelModel):
    contract_version: WorkerContractVersion = WORKER_CONTRACT_VERSION
    request_id: str
    code: str
    message: str
    retryable: bool = False
    details: dict[str, Any] | None = None


class WorkerStatusResponseV1(WorkerCamelModel):
    contract_version: WorkerContractVersion = WORKER_CONTRACT_VERSION
    status: Literal["ok"] = "ok"
    deepagents_available: bool
    deepagents_detail: str
    deepagents_enabled: bool


class WorkerStreamEvent(WorkerCamelModel):
    contract_version: WorkerContractVersion = WORKER_CONTRACT_VERSION
    request_id: str
    event_type: WorkerStreamEventType
    session_id: str


class WorkerStartedEvent(WorkerStreamEvent):
    event_type: Literal["roundtable.worker.v1.started"] = "roundtable.worker.v1.started"
    started_at: datetime


class WorkerMessageDeltaEvent(WorkerStreamEvent):
    event_type: Literal["roundtable.worker.v1.message.delta"] = "roundtable.worker.v1.message.delta"
    message_id: str
    persona_id: str | None = None
    sequence: int = Field(ge=1)
    text_delta: str


class WorkerMessageCompletedEvent(WorkerStreamEvent):
    event_type: Literal["roundtable.worker.v1.message.completed"] = "roundtable.worker.v1.message.completed"
    message_id: str
    persona_id: str | None = None
    role: Literal["moderator", "persona", "user", "system"]
    round_name: Literal["opening", "rebuttal", "closing", "synthesis", "follow_up", "system"]
    sequence: int = Field(ge=1)
    content: str


class WorkerArtifactUpdatedEvent(WorkerStreamEvent):
    event_type: Literal["roundtable.worker.v1.artifact.updated"] = "roundtable.worker.v1.artifact.updated"
    artifact_type: Literal["decision_artifact"] = "decision_artifact"
    payload: WorkerArtifact
    is_final: bool = True


class WorkerCompletedEvent(WorkerStreamEvent):
    event_type: Literal["roundtable.worker.v1.completed"] = "roundtable.worker.v1.completed"
    usage: dict[str, Any] = Field(default_factory=dict)
    completed_at: datetime


class WorkerErrorEvent(WorkerStreamEvent):
    event_type: Literal["roundtable.worker.v1.error"] = "roundtable.worker.v1.error"
    error: WorkerErrorV1
