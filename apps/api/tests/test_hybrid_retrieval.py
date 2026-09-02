from uuid import UUID, uuid4

import pytest

from apps.api.app.domain.rag.models import ChunkType, SemanticChunk
from packages.rag.researchos_rag.retrieval import (
    DenseRetriever,
    HybridRetriever,
    LexicalRetriever,
)
from packages.rag.researchos_rag.vector_store import ChromaVectorStore, VectorDocument


@pytest.mark.asyncio
async def test_lexical_retriever_finds_exact_scientific_terminology() -> None:
    organization_id = uuid4()
    project_id = uuid4()
    chunks = [
        chunk_fixture(
            organization_id,
            project_id,
            "ApoE4 carriers showed accelerated hippocampal atrophy.",
        ),
        chunk_fixture(
            organization_id,
            project_id,
            "Transformer encoders improved segmentation Dice scores.",
        ),
    ]

    results = await LexicalRetriever(chunks).search(
        organization_id=organization_id,
        project_id=project_id,
        query="ApoE4 hippocampal atrophy",
        limit=5,
    )

    assert [result.chunk_id for result in results] == [chunks[0].id]
    assert results[0].score > 0


@pytest.mark.asyncio
async def test_dense_retriever_finds_conceptual_match_from_vector_store() -> None:
    organization_id = uuid4()
    project_id = uuid4()
    close_chunk = chunk_fixture(
        organization_id,
        project_id,
        "Baseline MRI predicts cognitive decline.",
    )
    far_chunk = chunk_fixture(organization_id, project_id, "Cell culture protocol details.")
    store = ChromaVectorStore()
    await store.upsert(
        [
            VectorDocument.from_chunk(close_chunk, embedding=[1.0, 0.0]),
            VectorDocument.from_chunk(far_chunk, embedding=[0.0, 1.0]),
        ]
    )

    results = await DenseRetriever(store).search(
        organization_id=organization_id,
        project_id=project_id,
        query_embedding=[0.9, 0.1],
        limit=5,
    )

    assert [result.chunk_id for result in results] == [close_chunk.id, far_chunk.id]


@pytest.mark.asyncio
async def test_hybrid_retriever_uses_rank_fusion_and_keeps_tenant_scope() -> None:
    organization_id = uuid4()
    project_id = uuid4()
    other_project_id = uuid4()
    exact_chunk = chunk_fixture(
        organization_id,
        project_id,
        "ApoE4 status modifies biomarker response.",
    )
    conceptual_chunk = chunk_fixture(
        organization_id,
        project_id,
        "Genetic risk affects amyloid progression.",
    )
    leaked_chunk = chunk_fixture(
        organization_id,
        other_project_id,
        "ApoE4 private other project data.",
    )
    store = ChromaVectorStore()
    await store.upsert(
        [
            VectorDocument.from_chunk(exact_chunk, embedding=[0.2, 0.8]),
            VectorDocument.from_chunk(conceptual_chunk, embedding=[1.0, 0.0]),
            VectorDocument.from_chunk(leaked_chunk, embedding=[1.0, 0.0]),
        ]
    )
    retriever = HybridRetriever(
        dense=DenseRetriever(store),
        lexical=LexicalRetriever([exact_chunk, conceptual_chunk, leaked_chunk]),
    )

    results = await retriever.search(
        organization_id=organization_id,
        project_id=project_id,
        query="ApoE4 biomarker progression",
        query_embedding=[1.0, 0.0],
        limit=5,
    )

    assert [result.chunk_id for result in results] == [exact_chunk.id, conceptual_chunk.id]
    assert all(result.metadata["project_id"] == str(project_id) for result in results)
    assert all(result.score > 0 for result in results)


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
        section="Results",
        content=content,
        sequence_index=0,
    )
