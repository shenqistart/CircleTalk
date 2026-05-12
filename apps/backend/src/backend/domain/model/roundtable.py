"""Roundtable ORM models."""

from datetime import datetime, timezone

from core.database.base import Base
from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RoundtableSession(Base):
    __tablename__ = "roundtable_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    decision_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="ready", index=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    personas: Mapped[list["RoundtableSessionPersona"]] = relationship(cascade="all, delete-orphan", lazy="selectin")
    messages: Mapped[list["RoundtableMessage"]] = relationship(cascade="all, delete-orphan", lazy="selectin")
    artifacts: Mapped[list["RoundtableArtifact"]] = relationship(cascade="all, delete-orphan", lazy="selectin")


class RoundtablePersona(Base):
    __tablename__ = "roundtable_personas"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    skill_name: Mapped[str] = mapped_column(String(160), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)


class RoundtableSessionPersona(Base):
    __tablename__ = "roundtable_session_personas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("roundtable_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    persona_id: Mapped[str] = mapped_column(ForeignKey("roundtable_personas.id"), nullable=False, index=True)
    selection_source: Mapped[str] = mapped_column(String(20), nullable=False)
    selection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    persona: Mapped[RoundtablePersona] = relationship(lazy="selectin")


class RoundtableMessage(Base):
    __tablename__ = "roundtable_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("roundtable_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    persona_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    role: Mapped[str] = mapped_column(String(30), nullable=False)
    round_name: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    parent_message_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class RoundtableArtifact(Base):
    __tablename__ = "roundtable_artifacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("roundtable_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    memo: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    reasons_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    debate_map_json: Mapped[list[dict[str, str]]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)


class RoundtableTechnicalConfirmation(Base):
    __tablename__ = "roundtable_technical_confirmations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    confirmation_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    source_path: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
