from uuid import UUID, uuid4

import pytest

from packages.rag.researchos_rag.citation_answers import (
    CitationFirstAnswerComposer,
    CitationValidationError,
)
from packages.rag.researchos_rag.evidence_packs import EvidenceItem, EvidencePack, EvidenceSource


def test_answer_composer_requires_evidence_before_answering() -> None:
    pack = EvidencePack(query="Which model had the highest AUC?", items=[])

    answer = CitationFirstAnswerComposer().compose(pack)

    assert answer.answer == "Evidence unavailable for this question."
    assert answer.claims == []
    assert answer.citations == []


def test_answer_composer_creates_claims_with_real_citation_ids() -> None:
    item = evidence_item(
        content="Table 2 reports ViT achieved the highest AUC at 0.94.",
        page=9,
        section="Results",
    )
    pack = EvidencePack(query="Which model had the highest AUC?", items=[item])

    answer = CitationFirstAnswerComposer().compose(pack)

    assert answer.citations[0].id == "E1"
    assert answer.citations[0].chunk_id == item.chunk_id
    assert answer.citations[0].source.page == 9
    assert answer.claims[0].statement == item.content
    assert answer.claims[0].citation_ids == ["E1"]
    assert "[E1]" in answer.answer


def test_citation_validation_rejects_unknown_citation_ids() -> None:
    item = evidence_item(content="ApoE4 was associated with hippocampal atrophy.")
    pack = EvidencePack(query="What did the paper find?", items=[item])
    answer = CitationFirstAnswerComposer().compose(pack)
    invalid_answer = answer.model_copy(
        update={
            "claims": [
                answer.claims[0].model_copy(update={"citation_ids": ["E404"]}),
            ]
        }
    )

    with pytest.raises(CitationValidationError):
        CitationFirstAnswerComposer().validate(invalid_answer, pack)


def test_citation_validation_rejects_unsupported_claim_text() -> None:
    item = evidence_item(content="ApoE4 was associated with hippocampal atrophy.")
    pack = EvidencePack(query="What did the paper find?", items=[item])
    answer = CitationFirstAnswerComposer().compose(pack)
    invalid_answer = answer.model_copy(
        update={
            "claims": [
                answer.claims[0].model_copy(
                    update={"statement": "ApoE4 caused hippocampal atrophy."}
                ),
            ]
        }
    )

    with pytest.raises(CitationValidationError):
        CitationFirstAnswerComposer().validate(invalid_answer, pack)


def evidence_item(
    content: str,
    page: int = 1,
    section: str = "Abstract",
    document_id: UUID | None = None,
) -> EvidenceItem:
    return EvidenceItem(
        chunk_id=uuid4(),
        source=EvidenceSource(
            document_id=document_id or uuid4(),
            page=page,
            section=section,
            element_type="PARAGRAPH",
        ),
        content=content,
        retrieval_score=0.7,
        rerank_score=0.9,
    )
