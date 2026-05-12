"""Roundtable persistence repository."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from llm.roundtable import DecisionArtifact, SelectedPersona
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.model.roundtable import (
    RoundtableArtifact,
    RoundtableMessage,
    RoundtablePersonaModel,
    RoundtableSession,
    RoundtableSessionPersona,
)


class RoundtableRepository:
    """CRUD for sessions, personas, messages, and artifacts."""

    async def upsert_personas(self, session: AsyncSession, personas: list[SelectedPersona]) -> None:
        for persona in personas:
            existing = await session.get(RoundtablePersonaModel, persona.id)
            data = {
                "skill_name": persona.skill_name,
                "display_name": persona.display_name,
                "source_url": persona.source_url,
                "summary": persona.summary,
                "prompt_json": {"prompt": persona.prompt},
                "metadata_json": persona.metadata,
            }
            if existing is None:
                session.add(RoundtablePersonaModel(id=persona.id, **data))
            else:
                for key, value in data.items():
                    setattr(existing, key, value)
        await session.flush()

    async def create_session(
        self,
        session: AsyncSession,
        decision_prompt: str,
        selected_personas: list[SelectedPersona],
    ) -> RoundtableSession:
        session_id = str(uuid.uuid4())
        model = RoundtableSession(id=session_id, decision_prompt=decision_prompt, status="ready", metadata_json={})
        session.add(model)
        await self.upsert_personas(session, selected_personas)
        session.add_all(
            RoundtableSessionPersona(
                id=str(uuid.uuid4()),
                session_id=session_id,
                persona_id=persona.id,
                selection_source=persona.selection_source,
                selection_reason=persona.selection_reason,
                sequence=persona.sequence,
            )
            for persona in selected_personas
        )
        await session.flush()
        await session.refresh(model)
        return model

    async def get_session(self, session: AsyncSession, session_id: str) -> RoundtableSession | None:
        return await session.get(RoundtableSession, session_id)

    async def list_session_personas(self, session: AsyncSession, session_id: str) -> list[RoundtableSessionPersona]:
        result = await session.execute(
            select(RoundtableSessionPersona)
            .where(RoundtableSessionPersona.session_id == session_id)
            .order_by(RoundtableSessionPersona.sequence)
        )
        return list(result.scalars().all())

    async def list_messages(self, session: AsyncSession, session_id: str) -> list[RoundtableMessage]:
        result = await session.execute(
            select(RoundtableMessage)
            .where(RoundtableMessage.session_id == session_id)
            .order_by(RoundtableMessage.sequence, RoundtableMessage.created_at)
        )
        return list(result.scalars().all())

    async def get_latest_artifact(self, session: AsyncSession, session_id: str) -> RoundtableArtifact | None:
        result = await session.execute(
            select(RoundtableArtifact)
            .where(RoundtableArtifact.session_id == session_id)
            .order_by(RoundtableArtifact.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def replace_messages_and_artifact(
        self,
        session: AsyncSession,
        session_id: str,
        messages: list[dict[str, object]],
        artifact: DecisionArtifact,
    ) -> None:
        existing = await self.list_messages(session, session_id)
        next_sequence = len(existing) + 1
        for offset, message in enumerate(messages):
            session.add(
                RoundtableMessage(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    persona_id=message.get("persona_id"),
                    role=str(message["role"]),
                    round_name=str(message["round_name"]),
                    parent_message_id=message.get("parent_message_id"),
                    content=str(message["content"]),
                    sequence=next_sequence + offset,
                )
            )
        session.add(
            RoundtableArtifact(
                id=str(uuid.uuid4()),
                session_id=session_id,
                memo=artifact.memo,
                recommendation=artifact.recommendation,
                reasons_json=artifact.reasons,
                debate_map_json=artifact.debate_map,
            )
        )
        await self.update_status(session, session_id, "completed")

    async def append_follow_up(self, session: AsyncSession, session_id: str, content: str) -> None:
        existing = await self.list_messages(session, session_id)
        session.add(
            RoundtableMessage(
                id=str(uuid.uuid4()),
                session_id=session_id,
                role="moderator",
                round_name="follow_up",
                content=content,
                sequence=len(existing) + 1,
            )
        )
        await self.update_status(session, session_id, "completed")

    async def update_status(self, session: AsyncSession, session_id: str, status: str) -> None:
        model = await self.get_session(session, session_id)
        if model is None:
            msg = "roundtable session not found"
            raise ValueError(msg)
        model.status = status
        model.updated_at = datetime.now(UTC)
        await session.flush()
