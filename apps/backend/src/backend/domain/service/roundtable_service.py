"""Roundtable application service."""

import uuid
from collections.abc import AsyncIterator

from llm.roundtable import (
    answer_follow_up,
    list_personas,
    recommend_personas,
    run_with_deepagents_or_fallback,
    select_personas,
)
from llm.roundtable.schema import DecisionArtifact, RoundtablePersona, RoundtableTurn
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.model.roundtable import RoundtableArtifact, RoundtableMessage, RoundtableSession, RoundtableSessionPersona
from backend.domain.repository.roundtable_repository import RoundtableRepository
from backend.domain.schema.roundtable_schema import (
    CreateRoundtableSessionResponse,
    DecisionArtifactSchema,
    RoundtableMessageSchema,
    RoundtablePersonaSchema,
    RoundtableSessionSchema,
    SelectedPersonaSchema,
)


class RoundtableService:
    def __init__(self, repository: RoundtableRepository) -> None:
        self._repository = repository

    async def list_personas(self, session: AsyncSession) -> list[RoundtablePersonaSchema]:
        personas = list_personas()
        await self._repository.upsert_personas(session, [self._persona_record(persona) for persona in personas])
        return [self._persona_schema(persona) for persona in personas]

    async def recommend(self, decision_prompt: str) -> list[RoundtablePersonaSchema]:
        return [
            self._persona_schema(item.persona, item.reason)
            for item in recommend_personas(decision_prompt)
        ]

    async def create_session(
        self,
        db: AsyncSession,
        decision_prompt: str,
        persona_ids: list[str] | None,
    ) -> CreateRoundtableSessionResponse:
        personas, source, reasons = select_personas(decision_prompt, persona_ids)
        await self._repository.upsert_personas(db, [self._persona_record(persona) for persona in list_personas()])
        model = RoundtableSession(id=str(uuid.uuid4()), decision_prompt=decision_prompt, status="ready", metadata_json={})
        await self._repository.create_session(db, model)
        await self._repository.add_selected_personas(
            db,
            [
                RoundtableSessionPersona(
                    id=str(uuid.uuid4()),
                    session_id=model.id,
                    persona_id=persona.id,
                    skill_name=persona.skill_name,
                    display_name=persona.display_name,
                    summary=persona.summary,
                    selection_source=source,
                    selection_reason=reasons.get(persona.id),
                    sequence=index + 1,
                )
                for index, persona in enumerate(personas)
            ],
        )
        restored = await self._repository.get_session(db, model.id)
        if restored is None:
            msg = "created session could not be restored"
            raise RuntimeError(msg)
        return CreateRoundtableSessionResponse(
            session=self._session_schema(restored),
            recommended_personas=[self._persona_schema(persona, reasons.get(persona.id)) for persona in personas],
        )

    async def get_session(self, db: AsyncSession, session_id: str) -> RoundtableSessionSchema | None:
        model = await self._repository.get_session(db, session_id)
        return None if model is None else self._session_schema(model)

    async def stream_session(self, db: AsyncSession, session_id: str) -> AsyncIterator[str]:
        model = await self._repository.get_session(db, session_id)
        if model is None:
            msg = "session not found"
            raise ValueError(msg)
        personas = self._personas_from_model(model)
        await self._repository.update_status(db, session_id, "streaming")
        result = run_with_deepagents_or_fallback(model.decision_prompt, personas)
        messages = self._message_rows(session_id, result.transcript, start_sequence=len(model.messages) + 1)
        await self._repository.add_messages(db, messages)
        await self._repository.replace_artifact(db, self._artifact_row(session_id, result.artifact))
        await self._repository.update_status(db, session_id, "completed")
        for turn in result.transcript:
            yield f"{turn.content}\n\n"

    async def stream_follow_up(self, db: AsyncSession, session_id: str, question: str) -> AsyncIterator[str]:
        model = await self._repository.get_session(db, session_id)
        if model is None:
            msg = "session not found"
            raise ValueError(msg)
        artifact = model.artifacts[-1] if model.artifacts else None
        turn = answer_follow_up(question, self._personas_from_model(model), artifact.recommendation if artifact else None)
        await self._repository.add_messages(db, self._message_rows(session_id, [turn], start_sequence=len(model.messages) + 1))
        await self._repository.update_status(db, session_id, "completed")
        yield f"{turn.content}\n"

    def _persona_record(self, persona: RoundtablePersona) -> dict[str, object]:
        return {
            "id": persona.id,
            "skill_name": persona.skill_name,
            "display_name": persona.display_name,
            "source_url": persona.source_url,
            "summary": persona.summary,
            "prompt_json": {"system": persona.prompt},
            "metadata_json": persona.metadata,
        }

    def _persona_schema(self, persona: RoundtablePersona, reason: str | None = None) -> RoundtablePersonaSchema:
        return RoundtablePersonaSchema(
            id=persona.id,
            display_name=persona.display_name,
            skill_name=persona.skill_name,
            summary=persona.summary,
            selection_reason=reason,
        )

    def _personas_from_model(self, model: RoundtableSession) -> list[RoundtablePersona]:
        return [
            RoundtablePersona(
                id=row.persona_id,
                display_name=row.display_name,
                skill_name=row.skill_name,
                summary=row.summary,
                prompt=row.summary,
                selection_reason=row.selection_reason,
            )
            for row in model.selected_personas
        ]

    def _message_rows(self, session_id: str, turns: list[RoundtableTurn], start_sequence: int) -> list[RoundtableMessage]:
        return [
            RoundtableMessage(
                id=str(uuid.uuid4()),
                session_id=session_id,
                persona_id=turn.persona_id,
                persona_name=turn.persona_name,
                role=turn.role,
                round_name=turn.round_name,
                content=turn.content,
                sequence=start_sequence + index,
            )
            for index, turn in enumerate(turns)
        ]

    def _artifact_row(self, session_id: str, artifact: DecisionArtifact) -> RoundtableArtifact:
        return RoundtableArtifact(
            id=str(uuid.uuid4()),
            session_id=session_id,
            memo=artifact.memo,
            recommendation=artifact.recommendation,
            reasons_json=artifact.reasons,
            debate_map_json=artifact.debate_map,
        )

    def _artifact_schema(self, artifact: RoundtableArtifact | None) -> DecisionArtifactSchema | None:
        if artifact is None:
            return None
        return DecisionArtifactSchema(
            memo=artifact.memo,
            recommendation=artifact.recommendation,
            reasons=artifact.reasons_json,
            debate_map=artifact.debate_map_json,
        )

    def _session_schema(self, model: RoundtableSession) -> RoundtableSessionSchema:
        return RoundtableSessionSchema(
            id=model.id,
            decision_prompt=model.decision_prompt,
            status=model.status,
            selected_personas=[
                SelectedPersonaSchema(
                    id=row.persona_id,
                    display_name=row.display_name,
                    skill_name=row.skill_name,
                    summary=row.summary,
                    selection_reason=row.selection_reason,
                    selection_source=row.selection_source,
                    sequence=row.sequence,
                )
                for row in model.selected_personas
            ],
            transcript=[
                RoundtableMessageSchema(
                    id=row.id,
                    role=row.role,
                    content=row.content,
                    persona_id=row.persona_id,
                    persona_name=row.persona_name,
                    round_name=row.round_name,
                    sequence=row.sequence,
                    created_at=row.created_at,
                )
                for row in model.messages
            ],
            artifacts=self._artifact_schema(model.artifacts[-1] if model.artifacts else None),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
