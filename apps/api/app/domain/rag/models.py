from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class ChunkType(StrEnum):
    PARAGRAPH = "paragraph"
    SECTION = "section"
    TABLE = "table"
    FIGURE = "figure"
    EQUATION_CONTEXT = "equation-context"
    REFERENCE_CONTEXT = "reference-context"


class SemanticChunk(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    organization_id: UUID
    project_id: UUID
    document_id: UUID
    document_element_id: UUID
    chunk_type: ChunkType
    page: int = Field(ge=1)
    section: str | None
    content: str
    sequence_index: int = Field(ge=0)
