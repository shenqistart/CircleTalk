"""add roundtable tables

Revision ID: 20260512_0001
Revises: 
Create Date: 2026-05-12 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260512_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "roundtable_sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("decision_prompt", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_roundtable_sessions_status"), "roundtable_sessions", ["status"])
    op.create_table(
        "roundtable_personas",
        sa.Column("id", sa.String(length=80), nullable=False),
        sa.Column("skill_name", sa.String(length=160), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("prompt_json", sa.JSON(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "roundtable_technical_confirmations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("confirmation_json", sa.JSON(), nullable=False),
        sa.Column("source_path", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "roundtable_artifacts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("memo", sa.Text(), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("reasons_json", sa.JSON(), nullable=False),
        sa.Column("debate_map_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["roundtable_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_roundtable_artifacts_session_id"), "roundtable_artifacts", ["session_id"])
    op.create_table(
        "roundtable_messages",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("persona_id", sa.String(length=80), nullable=True),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column("round_name", sa.String(length=40), nullable=False),
        sa.Column("parent_message_id", sa.String(length=36), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["roundtable_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_roundtable_messages_persona_id"), "roundtable_messages", ["persona_id"])
    op.create_index(op.f("ix_roundtable_messages_round_name"), "roundtable_messages", ["round_name"])
    op.create_index(op.f("ix_roundtable_messages_session_id"), "roundtable_messages", ["session_id"])
    op.create_table(
        "roundtable_session_personas",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("persona_id", sa.String(length=80), nullable=False),
        sa.Column("selection_source", sa.String(length=20), nullable=False),
        sa.Column("selection_reason", sa.Text(), nullable=True),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["persona_id"], ["roundtable_personas.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["roundtable_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_roundtable_session_personas_persona_id"), "roundtable_session_personas", ["persona_id"])
    op.create_index(op.f("ix_roundtable_session_personas_session_id"), "roundtable_session_personas", ["session_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_roundtable_session_personas_session_id"), table_name="roundtable_session_personas")
    op.drop_index(op.f("ix_roundtable_session_personas_persona_id"), table_name="roundtable_session_personas")
    op.drop_table("roundtable_session_personas")
    op.drop_index(op.f("ix_roundtable_messages_session_id"), table_name="roundtable_messages")
    op.drop_index(op.f("ix_roundtable_messages_round_name"), table_name="roundtable_messages")
    op.drop_index(op.f("ix_roundtable_messages_persona_id"), table_name="roundtable_messages")
    op.drop_table("roundtable_messages")
    op.drop_index(op.f("ix_roundtable_artifacts_session_id"), table_name="roundtable_artifacts")
    op.drop_table("roundtable_artifacts")
    op.drop_table("roundtable_technical_confirmations")
    op.drop_table("roundtable_personas")
    op.drop_index(op.f("ix_roundtable_sessions_status"), table_name="roundtable_sessions")
    op.drop_table("roundtable_sessions")
