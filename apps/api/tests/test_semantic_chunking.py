from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from apps.api.app.domain.documents.models import ParsedDocument
from apps.api.app.domain.rag.models import ChunkType
from apps.api.app.repositories.chunks import InMemoryChunkRepository
from packages.documents.researchos_documents.schema import DocumentElement, DocumentElementType
from packages.rag.researchos_rag.chunking import SemanticChunker


def test_semantic_chunker_preserves_section_boundaries_and_metadata() -> None:
    organization_id = uuid4()
    project_id = uuid4()
    document_id = uuid4()
    document = ParsedDocument(
        id=document_id,
        organization_id=organization_id,
        project_id=project_id,
        file_id=uuid4(),
        title="Chunking Paper",
        page_count=2,
        elements=[
            DocumentElement(
                id=uuid4(),
                element_type=DocumentElementType.HEADING,
                page=1,
                text="Methods",
            ),
            DocumentElement(
                id=uuid4(),
                element_type=DocumentElementType.PARAGRAPH,
                page=1,
                section="Methods",
                text="We trained a compact encoder.",
            ),
            DocumentElement(
                id=uuid4(),
                element_type=DocumentElementType.HEADING,
                page=2,
                text="Results",
            ),
            DocumentElement(
                id=uuid4(),
                element_type=DocumentElementType.PARAGRAPH,
                page=2,
                section="Results",
                text="The model improved AUC.",
            ),
        ],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    chunks = SemanticChunker().chunk(document)

    assert [chunk.section for chunk in chunks] == ["Methods", "Methods", "Results", "Results"]
    assert chunks[1].content == "We trained a compact encoder."
    assert chunks[1].organization_id == organization_id
    assert chunks[1].project_id == project_id
    assert chunks[1].document_id == document_id
    assert chunks[1].chunk_type == ChunkType.PARAGRAPH
    assert chunks[1].page == 1


def test_semantic_chunker_keeps_tables_and_figure_captions_together() -> None:
    document = parsed_document_with_elements(
        [
            DocumentElement(
                id=uuid4(),
                element_type=DocumentElementType.TABLE,
                page=3,
                section="Results",
                text="Model | AUC\nCNN | 0.91\nViT | 0.94",
                caption="Table 1. Model performance.",
            ),
            DocumentElement(
                id=uuid4(),
                element_type=DocumentElementType.FIGURE,
                page=4,
                section="Architecture",
                caption="Figure 2. Encoder attention blocks.",
            ),
        ]
    )

    chunks = SemanticChunker().chunk(document)

    assert chunks[0].chunk_type == ChunkType.TABLE
    assert chunks[0].content == "Table 1. Model performance.\nModel | AUC\nCNN | 0.91\nViT | 0.94"
    assert chunks[1].chunk_type == ChunkType.FIGURE
    assert chunks[1].content == "Figure 2. Encoder attention blocks."


@pytest.mark.asyncio
async def test_chunk_repository_persists_chunks_with_tenant_scope() -> None:
    repository = InMemoryChunkRepository()
    organization_id = uuid4()
    project_id = uuid4()
    document = parsed_document_with_elements(
        [
            DocumentElement(
                id=uuid4(),
                element_type=DocumentElementType.PARAGRAPH,
                page=1,
                section="Abstract",
                text="A short abstract.",
            )
        ],
        organization_id=organization_id,
        project_id=project_id,
    )
    chunks = SemanticChunker().chunk(document)

    stored = await repository.replace_document_chunks(document.id, organization_id, chunks)
    visible = await repository.list_document_chunks(document.id, organization_id)
    blocked = await repository.list_document_chunks(document.id, uuid4())

    assert stored == chunks
    assert visible == chunks
    assert blocked == []


def parsed_document_with_elements(
    elements: list[DocumentElement],
    organization_id: UUID | None = None,
    project_id: UUID | None = None,
) -> ParsedDocument:
    return ParsedDocument(
        id=uuid4(),
        organization_id=organization_id or uuid4(),
        project_id=project_id or uuid4(),
        file_id=uuid4(),
        title="Fixture",
        page_count=4,
        elements=elements,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
