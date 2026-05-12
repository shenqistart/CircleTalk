"""Roundtable data access."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.domain.model.roundtable import (
    RoundtableArtifact,
    RoundtableMessage,
    RoundtablePersonaModel,
    RoundtableSession,
    RoundtableSessionPersona,
)


class RoundtableRepository:
    async def upsert_personas(self, session: AsyncSession, personas: Sequence[dict[str, object]]) -> None:
        for data in personas:
            existing = await session.get(RoundtablePersonaModel, data["id"])
            if existing is None:
                session.add(RoundtablePersonaModel(**data))
            else:
                for key, value in data.items():
                    setattr(existing, key, value)
        await session.flush()

    async def create_session(self, session: AsyncSession, model: RoundtableSession) -> RoundtableSession:
        session.add(model)
        await session.flush()
        return model

    async def add_selected_personas(self, session: AsyncSession, rows: Sequence[RoundtableSessionPersona]) -> None:
        session.add_all(rows)
        await session.flush()

    async def add_messages(self, session: AsyncSession, rows: Sequence[RoundtableMessage]) -> None:
        session.add_all(rows)
        await session.flush()

    async def replace_artifact(self, session: AsyncSession, artifact: RoundtableArtifact) -> None:
        session.add(artifact)
        await session.flush()

    async def get_session(self, session: AsyncSession, session_id: str) -> RoundtableSession | None:
        stmt = (
            select(RoundtableSession)
            .where(RoundtableSession.id == session_id)
            .options(
                selectinload(RoundtableSession.selected_personas),
                selectinload(RoundtableSession.messages),
                selectinload(RoundtableSession.artifacts),
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_status(self, session: AsyncSession, session_id: str, status: str) -> None:
        model = await session.get(RoundtableSession, session_id)
        if model is not None:
            model.status = status
        await session.flush()
