from uuid import UUID, uuid4

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.app.db.base import Base


class TableRecord(Base):
    __tablename__ = "tables"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id"),
        nullable=False,
        index=True,
    )
    document_element_id: Mapped[UUID] = mapped_column(
        ForeignKey("document_elements.id"),
        nullable=False,
        unique=True,
    )
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )
    page: Mapped[int] = mapped_column(Integer, nullable=False)
    section: Mapped[str | None] = mapped_column(String(500), nullable=True)
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    semantic_summary: Mapped[str] = mapped_column(Text, nullable=False)


class TableColumnRecord(Base):
    __tablename__ = "table_columns"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    table_id: Mapped[UUID] = mapped_column(ForeignKey("tables.id"), nullable=False, index=True)
    index: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)


class TableRowRecord(Base):
    __tablename__ = "table_rows"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    table_id: Mapped[UUID] = mapped_column(ForeignKey("tables.id"), nullable=False, index=True)
    index: Mapped[int] = mapped_column(Integer, nullable=False)


class TableCellRecord(Base):
    __tablename__ = "table_cells"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    table_id: Mapped[UUID] = mapped_column(ForeignKey("tables.id"), nullable=False, index=True)
    row_id: Mapped[UUID] = mapped_column(ForeignKey("table_rows.id"), nullable=False, index=True)
    row_index: Mapped[int] = mapped_column(Integer, nullable=False)
    column_index: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_value: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    numeric_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
