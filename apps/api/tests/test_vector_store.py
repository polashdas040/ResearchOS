from uuid import UUID, uuid4

import pytest

from apps.api.app.domain.rag.models import ChunkType, SemanticChunk
from packages.rag.researchos_rag.vector_store import (
    ChromaVectorStore,
    VectorDocument,
    VectorSearchQuery,
)


@pytest.mark.asyncio
async def test_vector_store_search_is_scoped_by_tenant_and_project() -> None:
    store = ChromaVectorStore()
    organization_id = uuid4()
    project_id = uuid4()
    other_project_id = uuid4()
    chunk = chunk_fixture(organization_id=organization_id, project_id=project_id, content="MRI AUC")
    leaked_chunk = chunk_fixture(
        organization_id=organization_id,
        project_id=other_project_id,
        content="MRI AUC private other project",
    )

    await store.upsert(
        [
            VectorDocument.from_chunk(chunk, embedding=[1.0, 0.0]),
            VectorDocument.from_chunk(leaked_chunk, embedding=[1.0, 0.0]),
        ]
    )

    results = await store.search(
        VectorSearchQuery(
            organization_id=organization_id,
            project_id=project_id,
            embedding=[1.0, 0.0],
            limit=10,
        )
    )

    assert [result.chunk_id for result in results] == [chunk.id]


@pytest.mark.asyncio
async def test_vector_store_delete_document_removes_only_scoped_chunks() -> None:
    store = ChromaVectorStore()
    organization_id = uuid4()
    project_id = uuid4()
    document_id = uuid4()
    chunk = chunk_fixture(
        organization_id=organization_id,
        project_id=project_id,
        document_id=document_id,
        content="target",
    )
    other_chunk = chunk_fixture(
        organization_id=uuid4(),
        project_id=project_id,
        document_id=document_id,
        content="other tenant target",
    )
    await store.upsert(
        [
            VectorDocument.from_chunk(chunk, embedding=[1.0, 0.0]),
            VectorDocument.from_chunk(other_chunk, embedding=[1.0, 0.0]),
        ]
    )

    await store.delete_document(organization_id, project_id, document_id)

    deleted_results = await store.search(
        VectorSearchQuery(
            organization_id=organization_id,
            project_id=project_id,
            embedding=[1.0, 0.0],
            limit=10,
        )
    )
    other_results = await store.search(
        VectorSearchQuery(
            organization_id=other_chunk.organization_id,
            project_id=project_id,
            embedding=[1.0, 0.0],
            limit=10,
        )
    )

    assert deleted_results == []
    assert [result.chunk_id for result in other_results] == [other_chunk.id]


def chunk_fixture(
    organization_id: UUID,
    project_id: UUID,
    content: str,
    document_id: UUID | None = None,
) -> SemanticChunk:
    return SemanticChunk(
        organization_id=organization_id,
        project_id=project_id,
        document_id=document_id or uuid4(),
        document_element_id=uuid4(),
        chunk_type=ChunkType.PARAGRAPH,
        page=1,
        section="Abstract",
        content=content,
        sequence_index=0,
    )
