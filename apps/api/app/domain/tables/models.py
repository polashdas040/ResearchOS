from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class TableCellKind(StrEnum):
    TEXT = "TEXT"
    NUMBER = "NUMBER"
    MISSING = "MISSING"


class TableColumn(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    index: int = Field(ge=0)
    name: str


class TableCell(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    row_index: int = Field(ge=0)
    column_index: int = Field(ge=0)
    raw_value: str
    normalized_value: str | None
    numeric_value: float | None
    kind: TableCellKind


class TableRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    index: int = Field(ge=0)
    cells: list[TableCell]


class ScientificTable(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    document_element_id: UUID
    organization_id: UUID | None = None
    project_id: UUID | None = None
    document_id: UUID | None = None
    page: int = Field(ge=1)
    section: str | None
    caption: str | None
    columns: list[TableColumn]
    rows: list[TableRow]
    semantic_summary: str


class TableAnswer(BaseModel):
    model_config = ConfigDict(frozen=True)

    answer: str
    source_table_id: UUID
    source_cell_ids: list[UUID]
