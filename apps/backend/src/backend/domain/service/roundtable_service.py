"""Roundtable application service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast

from llm.roundtable import (
    RoundtableOrchestrator,
    deepagents_status,
    load_personas,
    localize_persona,
    recommend_personas,
    select_personas,
)
from llm.roundtable.schema import DecisionArtifact, RoundtableMessage, SelectedPersona
from llm.roundtable.schema import RoundtablePersona as LlmPersona

from backend.domain.schema.roundtable_schema import (
    CreateRoundtableSessionRequest,
    CreateRoundtableSessionResponse,
    DecisionArtifactSchema,
    RoundtableLanguage,
    RoundtableMessageRole,
    RoundtableMessageSchema,
    RoundtablePersonaSchema,
    RoundtableRoundName,
    RoundtableSessionSchema,
    RoundtableSessionStatus,
    SelectedPersonaSchema,
)
from backend.domain.schema.roundtable_worker_schema import (
    FollowUpRequestV1,
    RecommendPersonasResponseV1,
    StartDiscussionRequestV1,
    WorkerArtifact,
    WorkerArtifactUpdatedEvent,
    WorkerCompletedEvent,
    WorkerErrorEvent,
    WorkerErrorV1,
    WorkerMessageCompletedEvent,
    WorkerMessageDeltaEvent,
    WorkerPersona,
    WorkerStartedEvent,
    WorkerStatusResponseV1,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from sqlalchemy.ext.asyncio import AsyncSession

    from backend.domain.model.roundtable import (
        RoundtableArtifact,
        RoundtableMessage,
        RoundtablePersonaModel,
        RoundtableSession,
        RoundtableSessionPersona,
    )
    from backend.domain.repository.roundtable_repository import RoundtableRepository


class RoundtableService:
    """Coordinates persona selection, persistence and request-scoped orchestration."""

    def __init__(self, repository: RoundtableRepository, orchestrator: RoundtableOrchestrator | None = None) -> None:
        self._repository = repository
        self._orchestrator = orchestrator or RoundtableOrchestrator()

    async def seed_personas(self, session: AsyncSession) -> None:
        await self._repository.upsert_personas(session, [_persona_to_seed(persona) for persona in load_personas()])

    async def list_personas(
        self,
        session: AsyncSession,
        language: RoundtableLanguage = "zh",
    ) -> list[RoundtablePersonaSchema]:
        await self.seed_personas(session)
        rows = await self._repository.list_personas(session)
        return [_persona_schema(row, language) for row in rows]

    async def recommend(
        self,
        decision_prompt: str,
        language: RoundtableLanguage = "zh",
    ) -> list[RoundtablePersonaSchema]:
        return [_roundtable_persona_schema(item) for item in recommend_personas(decision_prompt, language=language)]

    async def list_worker_personas(self, language: RoundtableLanguage = "zh") -> list[WorkerPersona]:
        return [_worker_persona_schema(localize_persona(persona, language), language) for persona in load_personas()]

    async def recommend_worker_personas(
        self,
        request_id: str,
        decision_prompt: str,
        language: RoundtableLanguage = "zh",
        max_personas: int = 3,
    ) -> RecommendPersonasResponseV1:
        personas = [
            _worker_persona_schema(item.persona, language)
            for item in recommend_personas(decision_prompt, language=language)[:max_personas]
        ]
        return RecommendPersonasResponseV1(request_id=request_id, personas=personas)

    async def worker_status(self, *, deepagents_enabled: bool) -> WorkerStatusResponseV1:
        status = deepagents_status()
        return WorkerStatusResponseV1(
            deepagents_available=status.available,
            deepagents_detail=status.detail,
            deepagents_enabled=deepagents_enabled,
        )

    async def stream_worker_discussion(
        self,
        request: StartDiscussionRequestV1,
    ) -> AsyncIterator[
        WorkerStartedEvent
        | WorkerMessageDeltaEvent
        | WorkerMessageCompletedEvent
        | WorkerArtifactUpdatedEvent
        | WorkerCompletedEvent
        | WorkerErrorEvent
    ]:
        yield WorkerStartedEvent(
            request_id=request.request_id,
            session_id=request.session_id,
            started_at=datetime.now(UTC),
        )
        selected = [_worker_selected_to_llm(persona) for persona in request.personas]
        sequence = max((message.sequence for message in request.prior_messages), default=0)
        try:
            async for event in self._orchestrator.stream(request.decision_prompt, selected, request.language):
                if event.text:
                    yield WorkerMessageDeltaEvent(
                        request_id=request.request_id,
                        session_id=request.session_id,
                        message_id=f"{request.session_id}:{sequence + 1}",
                        sequence=sequence + 1,
                        text_delta=event.text,
                    )
                if event.message is not None:
                    sequence += 1
                    yield _worker_message_completed_event(
                        request.request_id,
                        request.session_id,
                        sequence,
                        event.message,
                    )
                if event.artifact is not None:
                    yield WorkerArtifactUpdatedEvent(
                        request_id=request.request_id,
                        session_id=request.session_id,
                        payload=_worker_artifact_schema(event.artifact),
                        is_final=True,
                    )
            yield WorkerCompletedEvent(
                request_id=request.request_id,
                session_id=request.session_id,
                usage={"messages": sequence},
                completed_at=datetime.now(UTC),
            )
        except Exception as exc:
            yield _worker_error_event(request.request_id, request.session_id, exc)

    async def stream_worker_follow_up(
        self,
        request: FollowUpRequestV1,
    ) -> AsyncIterator[WorkerMessageDeltaEvent | WorkerMessageCompletedEvent | WorkerCompletedEvent | WorkerErrorEvent]:
        selected = [_worker_selected_to_llm(persona) for persona in request.personas]
        transcript = [message.content for message in request.messages]
        artifact = _worker_artifact_to_llm(request.artifact) if request.artifact else None
        sequence = max((message.sequence for message in request.messages), default=0)
        try:
            async for event in self._orchestrator.stream_follow_up(
                request.question,
                selected,
                transcript,
                artifact,
                request.language,
            ):
                if event.text:
                    yield WorkerMessageDeltaEvent(
                        request_id=request.request_id,
                        session_id=request.session_id,
                        message_id=f"{request.session_id}:{sequence + 1}",
                        sequence=sequence + 1,
                        text_delta=event.text,
                    )
                if event.message is not None:
                    sequence += 1
                    yield _worker_message_completed_event(
                        request.request_id,
                        request.session_id,
                        sequence,
                        event.message,
                    )
            yield WorkerCompletedEvent(
                request_id=request.request_id,
                session_id=request.session_id,
                usage={"messages": sequence},
                completed_at=datetime.now(UTC),
            )
        except Exception as exc:
            yield _worker_error_event(request.request_id, request.session_id, exc)

    async def create_session(
        self,
        session: AsyncSession,
        request: CreateRoundtableSessionRequest,
    ) -> CreateRoundtableSessionResponse:
        await self.seed_personas(session)
        selected = select_personas(request.decision_prompt, request.persona_ids, language=request.language)
        created = await self._repository.create_session(session, request.decision_prompt)
        await self._repository.add_message(
            session,
            created.id,
            role="user",
            content=request.decision_prompt,
            round_name="system",
            sequence=1,
        )
        await self._repository.replace_selected_personas(
            session,
            created.id,
            [_selected_to_row(item) for item in selected],
        )
        restored = await self.get_session(session, created.id)
        recommended = [_roundtable_persona_schema(item) for item in selected if item.selection_source == "auto"]
        return CreateRoundtableSessionResponse(session=restored, recommended_personas=recommended)

    async def get_session(self, session: AsyncSession, session_id: str) -> RoundtableSessionSchema:
        snapshot = await self._repository.snapshot(session, session_id)
        return _session_schema(snapshot)

    async def stream_discussion(
        self,
        session: AsyncSession,
        session_id: str,
        language: RoundtableLanguage = "zh",
    ) -> AsyncIterator[str]:
        snapshot = await self._repository.snapshot(session, session_id)
        session_model = cast("RoundtableSession", snapshot["session"])
        await self._repository.update_status(session, session_id, "streaming")
        selected = _selected_from_snapshot(snapshot, language)
        try:
            messages = cast("list[RoundtableMessage]", snapshot["messages"])
            sequence = max((message.sequence for message in messages), default=0)
            async for event in self._orchestrator.stream(session_model.decision_prompt, selected, language):
                if event.text:
                    yield event.text
                if event.message is not None:
                    sequence += 1
                    await self._repository.add_message(
                        session,
                        session_id,
                        role=event.message.role,
                        content=event.message.content,
                        round_name=event.message.round_name,
                        persona_id=event.message.persona_id,
                        sequence=sequence,
                    )
                if event.artifact is not None:
                    await self._repository.replace_artifact(session, session_id, event.artifact)
            await self._repository.update_status(session, session_id, "completed")
        except Exception:
            await self._repository.update_status(session, session_id, "error")
            failure_message = (
                "Roundtable discussion failed. Please try again later."
                if language == "en"
                else "圆桌讨论生成失败，请稍后重试。"
            )
            yield failure_message
            raise

    async def stream_follow_up(
        self,
        session: AsyncSession,
        session_id: str,
        question: str,
        language: RoundtableLanguage = "zh",
    ) -> AsyncIterator[str]:
        snapshot = await self._repository.snapshot(session, session_id)
        selected = _selected_from_snapshot(snapshot, language)
        messages = cast("list[RoundtableMessage]", snapshot["messages"])
        transcript = [message.content for message in messages]
        artifact_row = cast("RoundtableArtifact | None", snapshot["artifact"])
        artifact = _artifact_from_row(artifact_row) if artifact_row else None
        sequence = max((message.sequence for message in messages), default=0)
        row: RoundtableMessage | None = None
        async for event in self._orchestrator.stream_follow_up(question, selected, transcript, artifact, language):
            if event.text:
                yield event.text
            if event.message is not None:
                sequence += 1
                row = await self._repository.add_message(
                    session,
                    session_id,
                    role=event.message.role,
                    content=event.message.content,
                    round_name=event.message.round_name,
                    sequence=sequence,
                )
        await self._repository.update_status(session, session_id, "completed")
        if row is None:
            failure_message = (
                "Follow-up generation failed. Please try again later."
                if language == "en"
                else "追问生成失败，请稍后重试。"
            )
            yield failure_message

    async def mark_cancelled(self, session: AsyncSession, session_id: str) -> None:
        await self._repository.update_status(session, session_id, "cancelled")


def _persona_to_seed(persona: LlmPersona) -> dict[str, object]:
    return {
        "id": persona.id,
        "skill_name": persona.skill_name,
        "display_name": persona.display_name,
        "source_url": persona.source_url,
        "summary": persona.summary,
        "prompt_json": {"system": persona.prompt},
        "metadata_json": {"perspective_tags": list(persona.perspective_tags)},
    }


def _selected_to_row(item: SelectedPersona) -> dict[str, object]:
    return {
        "persona_id": item.persona.id,
        "selection_source": item.selection_source,
        "selection_reason": item.selection_reason,
        "sequence": item.sequence,
    }


def _persona_schema(row: RoundtablePersonaModel, language: RoundtableLanguage = "zh") -> RoundtablePersonaSchema:
    persona = localize_persona(_persona_from_row(row), language)
    return RoundtablePersonaSchema(
        id=persona.id,
        display_name=persona.display_name,
        skill_name=persona.skill_name,
        summary=persona.summary,
    )


def _roundtable_persona_schema(item: SelectedPersona) -> RoundtablePersonaSchema:
    return RoundtablePersonaSchema(
        id=item.persona.id,
        display_name=item.persona.display_name,
        skill_name=item.persona.skill_name,
        summary=item.persona.summary,
        selection_reason=item.selection_reason,
    )


def _worker_persona_schema(persona: LlmPersona, language: RoundtableLanguage = "zh") -> WorkerPersona:
    return WorkerPersona(
        id=persona.id,
        name=persona.display_name,
        title=persona.skill_name,
        description=persona.summary,
        expertise=list(persona.perspective_tags),
        language=language,
        metadata={"sourceUrl": persona.source_url} if persona.source_url else {},
    )


def _worker_selected_to_llm(persona: WorkerPersona) -> SelectedPersona:
    metadata = persona.metadata or {}
    return SelectedPersona(
        persona=LlmPersona(
            id=persona.id,
            skill_name=persona.title,
            display_name=persona.name,
            summary=persona.description,
            prompt=str(metadata.get("prompt", persona.description)),
            perspective_tags=tuple(persona.expertise),
            source_url=cast("str | None", metadata.get("sourceUrl")),
            selection_reason=getattr(persona, "selection_reason", None),
        ),
        selection_source=getattr(persona, "selection_source", "manual"),
        sequence=getattr(persona, "sequence", 1),
        selection_reason=getattr(persona, "selection_reason", None),
    )


def _worker_artifact_schema(artifact: DecisionArtifact) -> WorkerArtifact:
    return WorkerArtifact(
        memo=artifact.memo,
        recommendation=artifact.recommendation,
        reasons=list(artifact.reasons),
        debate_map=list(artifact.debate_map),
    )


def _worker_artifact_to_llm(artifact: WorkerArtifact) -> DecisionArtifact:
    return DecisionArtifact(
        memo=artifact.memo,
        recommendation=artifact.recommendation,
        reasons=tuple(artifact.reasons),
        debate_map=tuple(artifact.debate_map),
    )


def _worker_message_completed_event(
    request_id: str,
    session_id: str,
    sequence: int,
    message: RoundtableMessage,
) -> WorkerMessageCompletedEvent:
    return WorkerMessageCompletedEvent(
        request_id=request_id,
        session_id=session_id,
        message_id=f"{session_id}:{sequence}",
        persona_id=message.persona_id,
        role=cast("RoundtableMessageRole", message.role),
        round_name=cast("RoundtableRoundName", message.round_name),
        sequence=sequence,
        content=message.content,
    )


def _worker_error_event(request_id: str, session_id: str, exc: Exception) -> WorkerErrorEvent:
    return WorkerErrorEvent(
        request_id=request_id,
        session_id=session_id,
        error=WorkerErrorV1(
            request_id=request_id,
            code="roundtable_worker_error",
            message=str(exc) or "Roundtable worker failed.",
            retryable=True,
        ),
    )


def _persona_from_row(row: RoundtablePersonaModel) -> LlmPersona:
    return LlmPersona(
        id=row.id,
        skill_name=row.skill_name,
        display_name=row.display_name,
        summary=row.summary,
        prompt=str(row.prompt_json.get("system", row.summary)),
        perspective_tags=tuple(row.metadata_json.get("perspective_tags", ())),
        source_url=row.source_url,
    )


def _selected_from_snapshot(snapshot: dict[str, object], language: RoundtableLanguage = "zh") -> list[SelectedPersona]:
    selected = cast("list[RoundtableSessionPersona]", snapshot["selected"])
    personas = cast("dict[str, RoundtablePersonaModel]", snapshot["personas"])
    results: list[SelectedPersona] = []
    for item in selected:
        persona = localize_persona(_persona_from_row(personas[item.persona_id]), language)
        results.append(
            SelectedPersona(
                persona=persona,
                selection_source=item.selection_source,
                sequence=item.sequence,
                selection_reason=item.selection_reason,
            )
        )
    return results


def _message_schema(row: RoundtableMessage, persona_name_by_id: dict[str, str]) -> RoundtableMessageSchema:
    return RoundtableMessageSchema(
        id=row.id,
        role=cast("RoundtableMessageRole", row.role),
        content=row.content,
        persona_id=row.persona_id,
        persona_name=persona_name_by_id.get(row.persona_id or ""),
        round_name=cast("RoundtableRoundName", row.round_name),
        sequence=row.sequence,
        created_at=row.created_at,
    )


def _artifact_schema(row: RoundtableArtifact) -> DecisionArtifactSchema:
    return DecisionArtifactSchema(
        memo=row.memo,
        recommendation=row.recommendation,
        reasons=row.reasons_json,
        debate_map=row.debate_map_json,
    )


def _artifact_from_row(row: RoundtableArtifact) -> DecisionArtifact:
    return DecisionArtifact(
        memo=row.memo,
        recommendation=row.recommendation,
        reasons=tuple(row.reasons_json),
        debate_map=tuple(row.debate_map_json),
    )


def _session_schema(snapshot: dict[str, object]) -> RoundtableSessionSchema:
    session = cast("RoundtableSession", snapshot["session"])
    selected_rows = cast("list[RoundtableSessionPersona]", snapshot["selected"])
    personas = cast("dict[str, RoundtablePersonaModel]", snapshot["personas"])
    messages = cast("list[RoundtableMessage]", snapshot["messages"])
    artifact = cast("RoundtableArtifact | None", snapshot["artifact"])
    selected = [
        SelectedPersonaSchema(
            id=personas[item.persona_id].id,
            display_name=personas[item.persona_id].display_name,
            skill_name=personas[item.persona_id].skill_name,
            summary=personas[item.persona_id].summary,
            selection_reason=item.selection_reason,
            selection_source=item.selection_source,  # type: ignore[arg-type]
            sequence=item.sequence,
        )
        for item in selected_rows
    ]
    persona_name_by_id = {persona.id: persona.display_name for persona in personas.values()}
    return RoundtableSessionSchema(
        id=session.id,
        decision_prompt=session.decision_prompt,
        status=cast("RoundtableSessionStatus", session.status),
        selected_personas=selected,
        transcript=[_message_schema(row, persona_name_by_id) for row in messages],
        artifacts=_artifact_schema(artifact) if artifact else None,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )
