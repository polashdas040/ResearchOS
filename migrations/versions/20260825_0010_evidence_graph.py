"""Add evidence and claim graph.

Revision ID: 20260825_0010
Revises: 20260825_0009
Create Date: 2026-08-25 00:10:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260825_0010"
down_revision: str | None = "20260825_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "evidence",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("source_type", sa.String(length=100), nullable=False),
        sa.Column("source_id", sa.String(length=500), nullable=False),
        sa.Column("page", sa.Integer(), nullable=True),
        sa.Column("section", sa.String(length=500), nullable=True),
        sa.Column("quote_span", sa.Text(), nullable=True),
        sa.Column("extracted_statement", sa.Text(), nullable=False),
        sa.Column("reliability_score", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_evidence_organization_id"), "evidence", ["organization_id"])
    op.create_index(op.f("ix_evidence_project_id"), "evidence", ["project_id"])

    op.create_table(
        "claims",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("claim_type", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_claims_organization_id"), "claims", ["organization_id"])
    op.create_index(op.f("ix_claims_project_id"), "claims", ["project_id"])

    op.create_table(
        "claim_evidence_links",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("claim_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("relationship", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(["claim_id"], ["claims.id"]),
        sa.ForeignKeyConstraint(["evidence_id"], ["evidence.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "claim_id",
            "evidence_id",
            "relationship",
            name="uq_claim_evidence_relationship",
        ),
    )
    op.create_index(
        op.f("ix_claim_evidence_links_claim_id"),
        "claim_evidence_links",
        ["claim_id"],
    )
    op.create_index(
        op.f("ix_claim_evidence_links_evidence_id"),
        "claim_evidence_links",
        ["evidence_id"],
    )
    op.create_index(
        op.f("ix_claim_evidence_links_organization_id"),
        "claim_evidence_links",
        ["organization_id"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_claim_evidence_links_organization_id"),
        table_name="claim_evidence_links",
    )
    op.drop_index(op.f("ix_claim_evidence_links_evidence_id"), table_name="claim_evidence_links")
    op.drop_index(op.f("ix_claim_evidence_links_claim_id"), table_name="claim_evidence_links")
    op.drop_table("claim_evidence_links")
    op.drop_index(op.f("ix_claims_project_id"), table_name="claims")
    op.drop_index(op.f("ix_claims_organization_id"), table_name="claims")
    op.drop_table("claims")
    op.drop_index(op.f("ix_evidence_project_id"), table_name="evidence")
    op.drop_index(op.f("ix_evidence_organization_id"), table_name="evidence")
    op.drop_table("evidence")
