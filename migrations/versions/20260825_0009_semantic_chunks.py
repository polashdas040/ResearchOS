"""Add semantic document chunks.

Revision ID: 20260825_0009
Revises: 20260825_0008
Create Date: 2026-08-25 00:09:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260825_0009"
down_revision: str | None = "20260825_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "semantic_chunks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("document_element_id", sa.Uuid(), nullable=False),
        sa.Column("chunk_type", sa.String(length=64), nullable=False),
        sa.Column("page", sa.Integer(), nullable=False),
        sa.Column("section", sa.String(length=500), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sequence_index", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["document_element_id"], ["document_elements.id"]),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_semantic_chunks_chunk_type"),
        "semantic_chunks",
        ["chunk_type"],
    )
    op.create_index(
        op.f("ix_semantic_chunks_document_element_id"),
        "semantic_chunks",
        ["document_element_id"],
    )
    op.create_index(
        op.f("ix_semantic_chunks_document_id"),
        "semantic_chunks",
        ["document_id"],
    )
    op.create_index(
        op.f("ix_semantic_chunks_organization_id"),
        "semantic_chunks",
        ["organization_id"],
    )
    op.create_index(op.f("ix_semantic_chunks_project_id"), "semantic_chunks", ["project_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_semantic_chunks_project_id"), table_name="semantic_chunks")
    op.drop_index(op.f("ix_semantic_chunks_organization_id"), table_name="semantic_chunks")
    op.drop_index(op.f("ix_semantic_chunks_document_id"), table_name="semantic_chunks")
    op.drop_index(
        op.f("ix_semantic_chunks_document_element_id"),
        table_name="semantic_chunks",
    )
    op.drop_index(op.f("ix_semantic_chunks_chunk_type"), table_name="semantic_chunks")
    op.drop_table("semantic_chunks")
