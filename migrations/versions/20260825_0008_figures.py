"""Add scientific figure descriptions.

Revision ID: 20260825_0008
Revises: 20260825_0007
Create Date: 2026-08-25 00:08:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260825_0008"
down_revision: str | None = "20260825_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "figures",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("document_element_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("page", sa.Integer(), nullable=False),
        sa.Column("section", sa.String(length=500), nullable=True),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("image_sha256", sa.String(length=64), nullable=False),
        sa.Column("image_content_type", sa.String(length=100), nullable=False),
        sa.Column("figure_type", sa.String(length=100), nullable=True),
        sa.Column("labels", sa.JSON(), nullable=True),
        sa.Column("components", sa.JSON(), nullable=True),
        sa.Column("relationships", sa.JSON(), nullable=True),
        sa.Column("axes", sa.JSON(), nullable=True),
        sa.Column("trends", sa.JSON(), nullable=True),
        sa.Column("architecture_nodes", sa.JSON(), nullable=True),
        sa.Column("medical_anatomy", sa.JSON(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["document_element_id"], ["document_elements.id"]),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_element_id"),
    )
    op.create_index(op.f("ix_figures_document_id"), "figures", ["document_id"])
    op.create_index(op.f("ix_figures_organization_id"), "figures", ["organization_id"])
    op.create_index(op.f("ix_figures_project_id"), "figures", ["project_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_figures_project_id"), table_name="figures")
    op.drop_index(op.f("ix_figures_organization_id"), table_name="figures")
    op.drop_index(op.f("ix_figures_document_id"), table_name="figures")
    op.drop_table("figures")
