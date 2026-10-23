"""Add persistent research runtime.

Revision ID: 20260825_0012
Revises: 20260825_0011
Create Date: 2026-08-25 00:12:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260825_0012"
down_revision: str | None = "20260825_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "research_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("thread_id", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("state", sa.JSON(), nullable=False),
        sa.Column("checkpoint", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("thread_id", name="uq_research_runs_thread_id"),
    )
    op.create_index(op.f("ix_research_runs_organization_id"), "research_runs", ["organization_id"])
    op.create_index(op.f("ix_research_runs_project_id"), "research_runs", ["project_id"])
    op.create_index(op.f("ix_research_runs_status"), "research_runs", ["status"])
    op.create_index(op.f("ix_research_runs_user_id"), "research_runs", ["user_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_research_runs_user_id"), table_name="research_runs")
    op.drop_index(op.f("ix_research_runs_status"), table_name="research_runs")
    op.drop_index(op.f("ix_research_runs_project_id"), table_name="research_runs")
    op.drop_index(op.f("ix_research_runs_organization_id"), table_name="research_runs")
    op.drop_table("research_runs")
