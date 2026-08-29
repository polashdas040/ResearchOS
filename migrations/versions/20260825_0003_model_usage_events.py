"""Add model usage events.

Revision ID: 20260825_0003
Revises: 20260825_0002
Create Date: 2026-08-25 00:03:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260825_0003"
down_revision: str | None = "20260825_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "model_usage_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("message_id", sa.Uuid(), nullable=True),
        sa.Column("provider_name", sa.String(length=100), nullable=False),
        sa.Column("model_name", sa.String(length=200), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False),
        sa.Column("completion_tokens", sa.Integer(), nullable=False),
        sa.Column("total_tokens", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_model_usage_events_conversation_id"),
        "model_usage_events",
        ["conversation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_model_usage_events_message_id"),
        "model_usage_events",
        ["message_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_model_usage_events_organization_id"),
        "model_usage_events",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_model_usage_events_project_id"),
        "model_usage_events",
        ["project_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_model_usage_events_project_id"), table_name="model_usage_events")
    op.drop_index(op.f("ix_model_usage_events_organization_id"), table_name="model_usage_events")
    op.drop_index(op.f("ix_model_usage_events_message_id"), table_name="model_usage_events")
    op.drop_index(op.f("ix_model_usage_events_conversation_id"), table_name="model_usage_events")
    op.drop_table("model_usage_events")
