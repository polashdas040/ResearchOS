from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class FigureDescription(BaseModel):
    model_config = ConfigDict(frozen=True)

    figure_type: str
    labels: list[str]
    components: list[str]
    relationships: list[str]
    axes: list[str]
    trends: list[str]
    architecture_nodes: list[str]
    medical_anatomy: list[str]
    confidence: float = Field(ge=0, le=1)
    source_page: int = Field(ge=1)


class ScientificFigure(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    document_element_id: UUID
    organization_id: UUID | None = None
    project_id: UUID | None = None
    document_id: UUID | None = None
    page: int = Field(ge=1)
    section: str | None
    caption: str | None
    image_sha256: str
    image_content_type: str
    description: FigureDescription | None = None
