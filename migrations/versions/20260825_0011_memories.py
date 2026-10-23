"""Add project memory records.

Revision ID: 20260825_0011
Revises: 20260825_0010
Create Date: 2026-08-25 00:11:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260825_0011"
down_revision: str | None = "20260825_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "memories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=True),
        sa.Column("memory_class", sa.String(length=64), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("importance_score", sa.Float(), nullable=False),
        sa.Column("source_message_ids", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_memories_conversation_id"), "memories", ["conversation_id"])
    op.create_index(op.f("ix_memories_memory_class"), "memories", ["memory_class"])
    op.create_index(op.f("ix_memories_organization_id"), "memories", ["organization_id"])
    op.create_index(op.f("ix_memories_project_id"), "memories", ["project_id"])
    op.create_index(op.f("ix_memories_status"), "memories", ["status"])
    op.create_index(op.f("ix_memories_user_id"), "memories", ["user_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_memories_user_id"), table_name="memories")
    op.drop_index(op.f("ix_memories_status"), table_name="memories")
    op.drop_index(op.f("ix_memories_project_id"), table_name="memories")
    op.drop_index(op.f("ix_memories_organization_id"), table_name="memories")
    op.drop_index(op.f("ix_memories_memory_class"), table_name="memories")
    op.drop_index(op.f("ix_memories_conversation_id"), table_name="memories")
    op.drop_table("memories")
