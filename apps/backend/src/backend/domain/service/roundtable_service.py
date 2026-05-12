"""Roundtable application service."""

from collections.abc import AsyncIterator
from typing import cast

from llm.roundtable import RoundtableOrchestrator, load_personas, recommend_personas, select_personas
from llm.roundtable.schema import DecisionArtifact, RoundtablePersona as LlmPersona, SelectedPersona
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.model.roundtable import RoundtableArtifact, RoundtableMessage, RoundtablePersona, RoundtableSession
from backend.domain.repository.roundtable_repository import RoundtableRepository
from backend.domain.schema.roundtable_schema import (
    CreateRoundtableSessionRequest,
    CreateRoundtableSessionResponse,
    DecisionArtifactSchema,
    PersonaSelectionSource,
    RoundtableMessageRole,
    RoundtableMessageSchema,
    RoundtablePersonaSchema,
    RoundtableRoundName,
    RoundtableSessionSchema,
    RoundtableSessionStatus,
    SelectedPersonaSchema,
)


class RoundtableService:
    """Coordinates persona selection, persistence and request-scoped orchestration."""

    def __init__(self, repository: RoundtableRepository, orchestrator: RoundtableOrchestrator | None = None) -> None:
        self._repository = repository
        self._orchestrator = orchestrator or RoundtableOrchestrator()

    async def seed_personas(self, session: AsyncSession) -> None:
        await self._repository.upsert_personas(session, [_persona_to_seed(persona) for persona in load_personas()])

    async def list_personas(self, session: AsyncSession) -> list[RoundtablePersonaSchema]:
        await self.seed_personas(session)
        rows = await self._repository.list_personas(session)
        return [_persona_schema(row) for row in rows]

    async def recommend(self, decision_prompt: str) -> list[RoundtablePersonaSchema]:
        return [_selected_persona_schema(item) for item in recommend_personas(decision_prompt)]

    async def create_session(
        self,
        session: AsyncSession,
        request: CreateRoundtableSessionRequest,
    ) -> CreateRoundtableSessionResponse:
        selected = (
            select_manual_personas(persona_ids, self.personas()) if persona_ids else self.recommend(decision_prompt)
        )
        await self._repository.replace_selected_personas(session, created.id, [_selected_to_row(item) for item in selected])
        restored = await self._must_get_session(session, created.id)
        recommended = [_selected_persona_schema(item) for item in selected if item.selection_source == "auto"]
        return CreateRoundtableSessionResponse(session=_session_schema(restored), recommended_personas=recommended)

    async def get_session(self, session: AsyncSession, session_id: str) -> RoundtableSessionSchema:
        return _session_schema(await self._must_get_session(session, session_id))

    async def stream_discussion(self, session: AsyncSession, session_id: str) -> AsyncIterator[str]:
        restored = await self._must_get_session(session, session_id)
        await self._repository.update_status(session, session_id, "streaming")
        selected = _selected_from_session(restored)
        try:
            result = await self._orchestrator.run(restored.decision_prompt, selected)
            sequence = max((message.sequence for message in restored.messages), default=0)
            for generated in result.messages:
                sequence += 1
                await self._repository.add_message(
                    session,
                    session_id,
                    role=generated.role,
                    content=generated.content,
                    round_name=generated.round_name,
                    persona_id=generated.persona_id,
                    sequence=sequence,
                )
                yield f"{generated.content}\n\n"
            await self._repository.replace_artifact(session, session_id, result.artifact)
            await self._repository.update_status(session, session_id, "completed")
        except Exception:
            await self._repository.update_status(session, session_id, "error")
            yield "圆桌讨论生成失败，请稍后重试。"
            raise

    async def stream_follow_up(self, session: AsyncSession, session_id: str, question: str) -> AsyncIterator[str]:
        restored = await self._must_get_session(session, session_id)
        selected = _selected_from_session(restored)
        transcript = [message.content for message in sorted(restored.messages, key=lambda item: item.sequence)]
        artifact = _artifact_from_session(restored.artifacts[0]) if restored.artifacts else None
        generated = await self._orchestrator.follow_up(question, selected, transcript, artifact)
        sequence = max((message.sequence for message in restored.messages), default=0) + 1
        row = await self._repository.add_message(
            session,
            session_id,
            role=generated.role,
            content=generated.content,
            round_name="follow_up",
            sequence=sequence,
        )
        await self._repository.update_status(session, session_id, "completed")
        yield f"{row.content}\n"

    async def mark_cancelled(self, session: AsyncSession, session_id: str) -> None:
        await self._repository.update_status(session, session_id, "cancelled")

    async def _must_get_session(self, session: AsyncSession, session_id: str) -> RoundtableSession:
        restored = await self._repository.get_session(session, session_id)
        if restored is None:
            msg = "roundtable session not found"
            raise ValueError(msg)
        return restored

    async def follow_up(self, db: AsyncSession, session_id: str, question: str) -> AsyncIterator[str]:
        selected = await self._selected_personas(db, session_id)
        messages = await self._repository.list_messages(db, session_id)
        artifact_model = await self._repository.get_latest_artifact(db, session_id)
        artifact = self._artifact_from_model(artifact_model) if artifact_model else None
        response = self._agent._fallback.follow_up(
            question, selected, [message.content for message in messages], artifact
        )
        await self._repository.append_follow_up(db, session_id, response.content)
        yield response.content

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

    async def _build_session_schema(
        self,
        db: AsyncSession,
        model: RoundtableSession,
        selected_personas: list[SelectedPersona] | None = None,
    ) -> RoundtableSessionSchema:
        selected = selected_personas or await self._selected_personas(db, model.id)
        messages = await self._repository.list_messages(db, model.id)
        artifact = await self._repository.get_latest_artifact(db, model.id)
        return RoundtableSessionSchema(
            id=model.id,
            decision_prompt=model.decision_prompt,
            status=cast("RoundtableSessionStatus", model.status),
            selected_personas=[self._selected_schema(persona) for persona in selected],
            transcript=[self._message_schema(message) for message in messages],
            artifacts=self._artifact_schema(artifact) if artifact else None,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
        for item in personas
    ]


def _message_schema(row: RoundtableMessage, persona_name_by_id: dict[str, str]) -> RoundtableMessageSchema:
    return RoundtableMessageSchema(
        id=row.id,
        role=row.role,  # type: ignore[arg-type]
        content=row.content,
        persona_id=row.persona_id,
        persona_name=persona_name_by_id.get(row.persona_id or ""),
        round_name=row.round_name,
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


def _artifact_from_session(row: RoundtableArtifact) -> DecisionArtifact:
    return DecisionArtifact(
        memo=row.memo,
        recommendation=row.recommendation,
        reasons=tuple(row.reasons_json),
        debate_map=tuple(row.debate_map_json),
    )


def _session_schema(session: RoundtableSession) -> RoundtableSessionSchema:
    selected_rows = sorted(session.personas, key=lambda item: item.sequence)
    selected = [
        SelectedPersonaSchema(
            id=item.persona.id,
            display_name=item.persona.display_name,
            skill_name=item.persona.skill_name,
            summary=item.persona.summary,
            selection_reason=item.selection_reason,
            selection_source=item.selection_source,  # type: ignore[arg-type]
            sequence=item.sequence,
        )

    def _selected_schema(self, persona: SelectedPersona) -> SelectedPersonaSchema:
        return SelectedPersonaSchema(
            **self._persona_schema(persona).model_dump(),
            selection_source=cast("PersonaSelectionSource", persona.selection_source),
            sequence=persona.sequence,
        )

    def _message_schema(self, message: RoundtableMessage) -> RoundtableMessageSchema:
        return RoundtableMessageSchema(
            id=message.id,
            role=cast("RoundtableMessageRole", message.role),
            content=message.content,
            round_name=cast("RoundtableRoundName", message.round_name),
            sequence=message.sequence,
            created_at=message.created_at,
            persona_id=message.persona_id,
        )

    def _artifact_schema(self, artifact: RoundtableArtifact) -> DecisionArtifactSchema:
        return DecisionArtifactSchema(
            memo=artifact.memo,
            recommendation=artifact.recommendation,
            reasons=artifact.reasons_json,
            debate_map=artifact.debate_map_json,
        )

    def _artifact_from_model(self, artifact: RoundtableArtifact) -> DecisionArtifact:
        return DecisionArtifact(
            memo=artifact.memo,
            recommendation=artifact.recommendation,
            reasons=artifact.reasons_json,
            debate_map=artifact.debate_map_json,
        )
