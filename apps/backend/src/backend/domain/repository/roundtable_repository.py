"""Roundtable persistence repository."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import delete, select

from backend.domain.model.roundtable import (
    RoundtableArtifact,
    RoundtableMessage,
    RoundtablePersonaModel,
    RoundtableSession,
    RoundtableSessionPersona,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from llm.roundtable import DecisionArtifact
    from sqlalchemy.ext.asyncio import AsyncSession


class RoundtableRepository:
    """CRUD for sessions, personas, messages, and artifacts."""

    async def upsert_personas(self, session: AsyncSession, personas: Iterable[dict[str, object]]) -> None:
        for persona in personas:
            persona_id = str(persona["id"])
            existing = await session.get(RoundtablePersonaModel, persona_id)
            data = {
                "skill_name": str(persona["skill_name"]),
                "display_name": str(persona["display_name"]),
                "source_url": str(persona["source_url"]) if persona.get("source_url") else None,
                "summary": str(persona["summary"]),
                "prompt_json": persona.get("prompt_json", {}),
                "metadata_json": persona.get("metadata_json", {}),
            }
            if existing is None:
                session.add(RoundtablePersonaModel(id=persona_id, **data))
            else:
                for key, value in data.items():
                    setattr(existing, key, value)
        await session.flush()

    async def list_personas(self, session: AsyncSession) -> list[RoundtablePersonaModel]:
        result = await session.execute(select(RoundtablePersonaModel).order_by(RoundtablePersonaModel.display_name))
        return list(result.scalars().all())

    async def get_personas_by_ids(self, session: AsyncSession, persona_ids: list[str]) -> list[RoundtablePersonaModel]:
        result = await session.execute(select(RoundtablePersonaModel).where(RoundtablePersonaModel.id.in_(persona_ids)))
        rows = {row.id: row for row in result.scalars().all()}
        return [rows[persona_id] for persona_id in persona_ids if persona_id in rows]

    async def create_session(self, session: AsyncSession, decision_prompt: str) -> RoundtableSession:
        model = RoundtableSession(
            id=str(uuid.uuid4()),
            decision_prompt=decision_prompt,
            status="ready",
            metadata_json={},
        )
        session.add(model)
        await session.flush()
        await session.refresh(model)
        return model

    async def replace_selected_personas(
        self,
        session: AsyncSession,
        session_id: str,
        selected: Iterable[dict[str, object]],
    ) -> None:
        await session.execute(delete(RoundtableSessionPersona).where(RoundtableSessionPersona.session_id == session_id))
        rows: list[RoundtableSessionPersona] = []
        for item in selected:
            sequence_value = item["sequence"]
            rows.append(
                RoundtableSessionPersona(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    persona_id=str(item["persona_id"]),
                    selection_source=str(item["selection_source"]),
                    selection_reason=str(item["selection_reason"]) if item.get("selection_reason") else None,
                    sequence=sequence_value if isinstance(sequence_value, int) else int(str(sequence_value)),
                )
            )
        session.add_all(rows)
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

    async def replace_artifact(
        self,
        session: AsyncSession,
        session_id: str,
        artifact: DecisionArtifact,
    ) -> RoundtableArtifact:
        await session.execute(delete(RoundtableArtifact).where(RoundtableArtifact.session_id == session_id))
        model = RoundtableArtifact(
            id=str(uuid.uuid4()),
            session_id=session_id,
            memo=artifact.memo,
            recommendation=artifact.recommendation,
            reasons_json=list(artifact.reasons),
            debate_map_json=list(artifact.debate_map),
        )
        session.add(model)
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

    async def update_status(self, session: AsyncSession, session_id: str, status: str) -> None:
        model = await self.get_session(session, session_id)
        if model is None:
            msg = "roundtable session not found"
            raise ValueError(msg)
        model.status = status
        model.updated_at = datetime.now(UTC)
        await session.flush()

    async def snapshot(self, session: AsyncSession, session_id: str) -> dict[str, Any]:
        model = await self.get_session(session, session_id)
        if model is None:
            msg = "roundtable session not found"
            raise ValueError(msg)
        selected = await self.list_session_personas(session, session_id)
        persona_rows = await self.get_personas_by_ids(session, [item.persona_id for item in selected])
        return {
            "session": model,
            "selected": selected,
            "personas": {persona.id: persona for persona in persona_rows},
            "messages": await self.list_messages(session, session_id),
            "artifact": await self.get_latest_artifact(session, session_id),
        }
