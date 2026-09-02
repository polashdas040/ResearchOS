from uuid import UUID, uuid4

import pytest
from pydantic import TypeAdapter

from packages.rag.researchos_rag.evidence_packs import (
    EvidencePack,
    EvidencePackBuilder,
    KeywordReranker,
)
from packages.rag.researchos_rag.retrieval import RetrievalResult


@pytest.mark.asyncio
async def test_reranker_returns_deterministic_order_with_scores() -> None:
    document_id = uuid4()
    lower_relevance = retrieval_result(
        document_id=document_id,
        content="The cohort contains baseline MRI scans.",
        page=4,
        section="Methods",
    )
    higher_relevance = retrieval_result(
        document_id=document_id,
        content="ApoE4 biomarker progression was associated with hippocampal atrophy.",
        page=7,
        section="Results",
    )

    reranked = await KeywordReranker().rerank(
        query="ApoE4 biomarker hippocampal",
        candidates=[lower_relevance, higher_relevance],
        limit=10,
    )

    assert [item.chunk_id for item in reranked] == [
        higher_relevance.chunk_id,
        lower_relevance.chunk_id,
    ]
    assert reranked[0].rerank_score > reranked[1].rerank_score


@pytest.mark.asyncio
async def test_evidence_pack_preserves_source_page_section_and_scores() -> None:
    document_id = uuid4()
    candidate = retrieval_result(
        document_id=document_id,
        content="Table 2 reports ViT achieved the highest AUC.",
        page=9,
        section="Results",
        metadata={"element_type": "TABLE", "source_id": "table-2"},
    )

    pack = await EvidencePackBuilder(KeywordReranker()).build(
        query="highest AUC",
        candidates=[candidate],
        limit=5,
    )

    assert pack.query == "highest AUC"
    assert len(pack.items) == 1
    assert pack.items[0].source.document_id == document_id
    assert pack.items[0].source.page == 9
    assert pack.items[0].source.section == "Results"
    assert pack.items[0].source.element_type == "TABLE"
    assert pack.items[0].content == candidate.content
    assert pack.items[0].retrieval_score == candidate.score
    assert pack.items[0].rerank_score > 0


@pytest.mark.asyncio
async def test_evidence_pack_is_serializable_and_limited() -> None:
    candidates = [
        retrieval_result(content="ApoE4 biomarker hippocampal atrophy.", page=1),
        retrieval_result(content="ApoE4 biomarker amyloid progression.", page=2),
        retrieval_result(content="Unrelated scanner calibration.", page=3),
    ]

    pack = await EvidencePackBuilder(KeywordReranker()).build(
        query="ApoE4 biomarker",
        candidates=candidates,
        limit=2,
    )
    serialized = pack.model_dump(mode="json")
    loaded = TypeAdapter(EvidencePack).validate_python(serialized)

    assert len(pack.items) == 2
    assert loaded == pack
    assert [item.source.page for item in pack.items] == [1, 2]


def retrieval_result(
    content: str,
    page: int,
    document_id: UUID | None = None,
    section: str = "Abstract",
    metadata: dict[str, str | int] | None = None,
) -> RetrievalResult:
    chunk_id = uuid4()
    resolved_document_id = document_id or uuid4()
    merged_metadata: dict[str, str | int] = {
        "tenant_id": str(uuid4()),
        "project_id": str(uuid4()),
        "document_id": str(resolved_document_id),
        "page": page,
        "section": section,
        "element_type": "PARAGRAPH",
    }
    if metadata:
        merged_metadata.update(metadata)
    return RetrievalResult(
        chunk_id=chunk_id,
        document_id=resolved_document_id,
        content=content,
        score=0.42,
        metadata=merged_metadata,
        dense_score=0.31,
        lexical_score=2.0,
    )
