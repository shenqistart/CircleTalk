"""Roundtable ORM models."""

from datetime import datetime

from core.database.base import Base
from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship


class RoundtablePersonaModel(Base):
    __tablename__ = "roundtable_personas"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    skill_name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class RoundtableSession(Base):
    __tablename__ = "roundtable_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    decision_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ready", index=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    selected_personas: Mapped[list["RoundtableSessionPersona"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="RoundtableSessionPersona.sequence",
    )
    messages: Mapped[list["RoundtableMessage"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="RoundtableMessage.sequence",
    )
    artifacts: Mapped[list["RoundtableArtifact"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )


class RoundtableSessionPersona(Base):
    __tablename__ = "roundtable_session_personas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("roundtable_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    persona_id: Mapped[str] = mapped_column(String(64), nullable=False)
    skill_name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    selection_source: Mapped[str] = mapped_column(String(16), nullable=False)
    selection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session: Mapped[RoundtableSession] = relationship(back_populates="selected_personas")


class RoundtableMessage(Base):
    __tablename__ = "roundtable_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("roundtable_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    persona_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    persona_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    round_name: Mapped[str] = mapped_column(String(32), nullable=False)
    parent_message_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session: Mapped[RoundtableSession] = relationship(back_populates="messages")


class RoundtableArtifact(Base):
    __tablename__ = "roundtable_artifacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("roundtable_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    memo: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    reasons_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    debate_map_json: Mapped[list[dict[str, str]]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    session: Mapped[RoundtableSession] = relationship(back_populates="artifacts")


class RoundtableTechnicalConfirmation(Base):
    __tablename__ = "roundtable_technical_confirmations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    confirmation_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    source_path: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
