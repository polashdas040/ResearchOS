from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from packages.documents.researchos_documents.schema import (
    BoundingBox,
    DocumentElement,
    DocumentElementType,
    StructuredDocument,
)


class ParsedDocument(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    project_id: UUID
    organization_id: UUID
    file_id: UUID
    title: str | None
    page_count: int = Field(ge=1)
    elements: list[DocumentElement]
    created_at: datetime
    updated_at: datetime


__all__ = [
    "BoundingBox",
    "DocumentElement",
    "DocumentElementType",
    "ParsedDocument",
    "StructuredDocument",
]
