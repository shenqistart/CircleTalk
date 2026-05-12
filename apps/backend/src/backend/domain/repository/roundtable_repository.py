"""Roundtable repository operations."""

import uuid
from collections.abc import Iterable

from llm.roundtable.schema import DecisionArtifact
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.domain.model.roundtable import (
    RoundtableArtifact,
    RoundtableMessage,
    RoundtablePersona,
    RoundtableSession,
    RoundtableSessionPersona,
    utc_now,
)


class RoundtableRepository:
    """Data access for roundtable sessions, personas, messages and artifacts."""

    async def upsert_personas(self, session: AsyncSession, personas: Iterable[dict[str, object]]) -> None:
        for persona in personas:
            existing = await session.get(RoundtablePersona, str(persona["id"]))
            data = {
                "id": str(persona["id"]),
                "skill_name": str(persona["skill_name"]),
                "display_name": str(persona["display_name"]),
                "source_url": str(persona["source_url"]) if persona.get("source_url") else None,
                "summary": str(persona["summary"]),
                "prompt_json": persona.get("prompt_json", {}),
                "metadata_json": persona.get("metadata_json", {}),
            }
            if existing is None:
                session.add(RoundtablePersona(**data))
            else:
                for key, value in data.items():
                    setattr(existing, key, value)
        await session.flush()

    async def list_personas(self, session: AsyncSession) -> list[RoundtablePersona]:
        result = await session.execute(select(RoundtablePersona).order_by(RoundtablePersona.display_name))
        return list(result.scalars().all())

    async def create_session(self, session: AsyncSession, decision_prompt: str) -> RoundtableSession:
        instance = RoundtableSession(id=str(uuid.uuid4()), decision_prompt=decision_prompt, status="ready")
        session.add(instance)
        await session.flush()
        await session.refresh(instance)
        return instance

    async def replace_selected_personas(
        self,
        session: AsyncSession,
        session_id: str,
        selected: list[dict[str, object]],
    ) -> None:
        await session.execute(delete(RoundtableSessionPersona).where(RoundtableSessionPersona.session_id == session_id))
        session.add_all(
            RoundtableSessionPersona(
                id=str(uuid.uuid4()),
                session_id=session_id,
                persona_id=str(item["persona_id"]),
                selection_source=str(item["selection_source"]),
                selection_reason=str(item["selection_reason"]) if item.get("selection_reason") else None,
                sequence=int(item["sequence"]),
            )
            for item in selected
        )
        await session.flush()

    async def add_message(
        self,
        session: AsyncSession,
        session_id: str,
        *,
        role: str,
        content: str,
        round_name: str,
        sequence: int,
        persona_id: str | None = None,
        parent_message_id: str | None = None,
    ) -> RoundtableMessage:
        message = RoundtableMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            persona_id=persona_id,
            role=role,
            round_name=round_name,
            parent_message_id=parent_message_id,
            content=content,
            sequence=sequence,
        )
        session.add(message)
        await session.flush()
        await session.refresh(message)
        return message

    async def replace_artifact(self, session: AsyncSession, session_id: str, artifact: DecisionArtifact) -> RoundtableArtifact:
        await session.execute(delete(RoundtableArtifact).where(RoundtableArtifact.session_id == session_id))
        instance = RoundtableArtifact(
            id=str(uuid.uuid4()),
            session_id=session_id,
            memo=artifact.memo,
            recommendation=artifact.recommendation,
            reasons_json=list(artifact.reasons),
            debate_map_json=list(artifact.debate_map),
        )
        session.add(instance)
        await session.flush()
        await session.refresh(instance)
        return instance

    async def update_status(self, session: AsyncSession, session_id: str, status: str) -> None:
        instance = await session.get(RoundtableSession, session_id)
        if instance is None:
            msg = "roundtable session not found"
            raise ValueError(msg)
        instance.status = status
        instance.updated_at = utc_now()
        await session.flush()

    async def get_session(self, session: AsyncSession, session_id: str) -> RoundtableSession | None:
        result = await session.execute(
            select(RoundtableSession)
            .options(
                selectinload(RoundtableSession.personas).selectinload(RoundtableSessionPersona.persona),
                selectinload(RoundtableSession.messages),
                selectinload(RoundtableSession.artifacts),
            )
            .where(RoundtableSession.id == session_id)
        )
        return result.scalar_one_or_none()
