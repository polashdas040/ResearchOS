from uuid import uuid4

import pytest

from apps.api.app.repositories.figures import InMemoryFigureRepository
from packages.documents.researchos_documents.figures import (
    DeterministicFigureVisionModel,
    FigureExtractor,
    FigureIntelligenceService,
)
from packages.documents.researchos_documents.schema import DocumentElement, DocumentElementType


def test_figure_extractor_links_caption_page_and_image_bytes() -> None:
    element_id = uuid4()
    extractor = FigureExtractor()
    figure = extractor.extract(
        DocumentElement(
            id=element_id,
            element_type=DocumentElementType.FIGURE,
            page=7,
            section="Architecture",
            caption="Figure 2. Transformer encoder architecture with attention blocks.",
        ),
        image_bytes=b"fake-image-bytes",
        image_content_type="image/png",
    )

    assert figure.document_element_id == element_id
    assert figure.page == 7
    assert figure.section == "Architecture"
    assert figure.caption == "Figure 2. Transformer encoder architecture with attention blocks."
    assert figure.image_content_type == "image/png"
    assert figure.image_sha256


@pytest.mark.asyncio
async def test_figure_intelligence_creates_structured_description() -> None:
    service = FigureIntelligenceService(vision_model=DeterministicFigureVisionModel())
    figure = FigureExtractor().extract(
        DocumentElement(
            id=uuid4(),
            element_type=DocumentElementType.FIGURE,
            page=2,
            section="Methods",
            caption="Figure 1. Workflow diagram showing preprocessing and classifier.",
        ),
        image_bytes=b"fake-image-bytes",
        image_content_type="image/png",
    )

    description = await service.describe(figure)

    assert description.figure_type == "workflow"
    assert description.labels == ["preprocessing", "classifier"]
    assert description.source_page == 2
    assert description.confidence == 0.7


@pytest.mark.asyncio
async def test_figure_repository_persists_description_with_tenant_scope() -> None:
    repository = InMemoryFigureRepository()
    organization_id = uuid4()
    blocked_organization_id = uuid4()
    project_id = uuid4()
    document_id = uuid4()
    figure = FigureExtractor().extract(
        DocumentElement(
            id=uuid4(),
            element_type=DocumentElementType.FIGURE,
            page=3,
            section="Results",
            caption="Figure 3. ROC trend across models.",
        ),
        image_bytes=b"fake-image-bytes",
        image_content_type="image/png",
    )
    description = await FigureIntelligenceService(DeterministicFigureVisionModel()).describe(figure)

    stored = await repository.create_figure(
        organization_id=organization_id,
        project_id=project_id,
        document_id=document_id,
        figure=figure,
        description=description,
    )
    loaded = await repository.get_figure(stored.id, organization_id)
    blocked = await repository.get_figure(stored.id, blocked_organization_id)

    assert loaded is not None
    assert loaded.description is not None
    assert loaded.description.figure_type == "chart"
    assert blocked is None
