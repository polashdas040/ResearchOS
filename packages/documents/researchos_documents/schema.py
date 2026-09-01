from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DocumentElementType(StrEnum):
    TITLE = "TITLE"
    ABSTRACT = "ABSTRACT"
    HEADING = "HEADING"
    PARAGRAPH = "PARAGRAPH"
    TABLE = "TABLE"
    FIGURE = "FIGURE"
    EQUATION = "EQUATION"
    REFERENCE = "REFERENCE"
    CAPTION = "CAPTION"


class BoundingBox(BaseModel):
    model_config = ConfigDict(frozen=True)

    x0: float
    y0: float
    x1: float
    y1: float


class DocumentElement(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID | None = None
    element_type: DocumentElementType
    page: int = Field(ge=1)
    section: str | None = None
    bbox: BoundingBox | None = None
    text: str | None = None
    caption: str | None = None
    parent_id: UUID | None = None


class StructuredDocument(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str | None
    page_count: int = Field(ge=1)
    elements: list[DocumentElement]
