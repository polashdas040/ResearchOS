"""Add scientific table structures.

Revision ID: 20260825_0007
Revises: 20260825_0006
Create Date: 2026-08-25 00:07:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260825_0007"
down_revision: str | None = "20260825_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tables",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("document_element_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("page", sa.Integer(), nullable=False),
        sa.Column("section", sa.String(length=500), nullable=True),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("semantic_summary", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["document_element_id"], ["document_elements.id"]),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_element_id"),
    )
    op.create_index(op.f("ix_tables_document_id"), "tables", ["document_id"])
    op.create_index(op.f("ix_tables_organization_id"), "tables", ["organization_id"])
    op.create_index(op.f("ix_tables_project_id"), "tables", ["project_id"])
    op.create_table(
        "table_columns",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("table_id", sa.Uuid(), nullable=False),
        sa.Column("index", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.ForeignKeyConstraint(["table_id"], ["tables.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_table_columns_table_id"), "table_columns", ["table_id"])
    op.create_table(
        "table_rows",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("table_id", sa.Uuid(), nullable=False),
        sa.Column("index", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["table_id"], ["tables.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_table_rows_table_id"), "table_rows", ["table_id"])
    op.create_table(
        "table_cells",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("table_id", sa.Uuid(), nullable=False),
        sa.Column("row_id", sa.Uuid(), nullable=False),
        sa.Column("row_index", sa.Integer(), nullable=False),
        sa.Column("column_index", sa.Integer(), nullable=False),
        sa.Column("raw_value", sa.Text(), nullable=False),
        sa.Column("normalized_value", sa.Text(), nullable=True),
        sa.Column("numeric_value", sa.Float(), nullable=True),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(["row_id"], ["table_rows.id"]),
        sa.ForeignKeyConstraint(["table_id"], ["tables.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_table_cells_row_id"), "table_cells", ["row_id"])
    op.create_index(op.f("ix_table_cells_table_id"), "table_cells", ["table_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_table_cells_table_id"), table_name="table_cells")
    op.drop_index(op.f("ix_table_cells_row_id"), table_name="table_cells")
    op.drop_table("table_cells")
    op.drop_index(op.f("ix_table_rows_table_id"), table_name="table_rows")
    op.drop_table("table_rows")
    op.drop_index(op.f("ix_table_columns_table_id"), table_name="table_columns")
    op.drop_table("table_columns")
    op.drop_index(op.f("ix_tables_project_id"), table_name="tables")
    op.drop_index(op.f("ix_tables_organization_id"), table_name="tables")
    op.drop_index(op.f("ix_tables_document_id"), table_name="tables")
    op.drop_table("tables")
