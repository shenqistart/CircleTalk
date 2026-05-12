"""Roundtable application service."""

from collections.abc import AsyncIterator

from llm.roundtable import (
    DecisionArtifact,
    RoundtableDeepAgentAdapter,
    RoundtablePersona,
    SelectedPersona,
    load_default_personas,
    recommend_personas,
    select_manual_personas,
)
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.model.roundtable import RoundtableArtifact, RoundtableMessage, RoundtableSession
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
    """Coordinates persona choice, orchestration, persistence, and restore."""

    def __init__(self, repository: RoundtableRepository, agent: RoundtableDeepAgentAdapter | None = None) -> None:
        self._repository = repository
        self._agent = agent or RoundtableDeepAgentAdapter()

    def personas(self) -> list[RoundtablePersona]:
        return load_default_personas()

    def recommend(self, decision_prompt: str) -> list[SelectedPersona]:
        return recommend_personas(decision_prompt, self.personas())

    async def create_session(
        self,
        db: AsyncSession,
        decision_prompt: str,
        persona_ids: list[str],
    ) -> CreateRoundtableSessionResponse:
        selected = (
            select_manual_personas(persona_ids, self.personas())
            if persona_ids
            else self.recommend(decision_prompt)
        )
        model = await self._repository.create_session(db, decision_prompt, selected)
        schema = await self._build_session_schema(db, model, selected_personas=selected)
        recommended = [] if persona_ids else [self._persona_schema(persona) for persona in selected]
        return CreateRoundtableSessionResponse(session=schema, recommended_personas=recommended)

    async def get_session(self, db: AsyncSession, session_id: str) -> RoundtableSessionSchema | None:
        model = await self._repository.get_session(db, session_id)
        if model is None:
            return None
        return await self._build_session_schema(db, model)

    async def stream_session(self, db: AsyncSession, session_id: str) -> AsyncIterator[str]:
        model = await self._repository.get_session(db, session_id)
        if model is None:
            msg = "roundtable session not found"
            raise ValueError(msg)
        await self._repository.update_status(db, session_id, "streaming")
        selected = await self._selected_personas(db, session_id)
        try:
            result = self._agent.run(model.decision_prompt, selected)
            await self._repository.replace_messages_and_artifact(
                db,
                session_id,
                [message.model_dump() for message in result.messages],
                result.artifact,
            )
            for message in result.messages:
                yield f"{message.content}\n\n"
        except Exception:
            await self._repository.update_status(db, session_id, "error")
            yield "圆桌讨论生成失败，请稍后重试。"

    async def follow_up(self, db: AsyncSession, session_id: str, question: str) -> AsyncIterator[str]:
        selected = await self._selected_personas(db, session_id)
        messages = await self._repository.list_messages(db, session_id)
        artifact_model = await self._repository.get_latest_artifact(db, session_id)
        artifact = self._artifact_from_model(artifact_model) if artifact_model else None
        response = self._agent._fallback.follow_up(question, selected, [message.content for message in messages], artifact)
        await self._repository.append_follow_up(db, session_id, response.content)
        yield response.content

    async def _selected_personas(self, db: AsyncSession, session_id: str) -> list[SelectedPersona]:
        links = await self._repository.list_session_personas(db, session_id)
        by_id = {persona.id: persona for persona in self.personas()}
        selected: list[SelectedPersona] = []
        for link in links:
            persona = by_id[link.persona_id]
            selected.append(
                SelectedPersona(
                    **persona.model_dump(exclude={"selection_reason"}),
                    selection_source=link.selection_source,
                    selection_reason=link.selection_reason,
                    sequence=link.sequence,
                )
            )
        return selected

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
            status=model.status,
            selected_personas=[self._selected_schema(persona) for persona in selected],
            transcript=[self._message_schema(message) for message in messages],
            artifacts=self._artifact_schema(artifact) if artifact else None,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _persona_schema(self, persona: RoundtablePersona | SelectedPersona) -> RoundtablePersonaSchema:
        return RoundtablePersonaSchema(
            id=persona.id,
            display_name=persona.display_name,
            skill_name=persona.skill_name,
            summary=persona.summary,
            selection_reason=persona.selection_reason,
        )

    def _selected_schema(self, persona: SelectedPersona) -> SelectedPersonaSchema:
        return SelectedPersonaSchema(**self._persona_schema(persona).model_dump(), selection_source=persona.selection_source, sequence=persona.sequence)

    def _message_schema(self, message: RoundtableMessage) -> RoundtableMessageSchema:
        return RoundtableMessageSchema(
            id=message.id,
            role=message.role,
            content=message.content,
            round_name=message.round_name,
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
        return DecisionArtifact(memo=artifact.memo, recommendation=artifact.recommendation, reasons=artifact.reasons_json, debate_map=artifact.debate_map_json)
