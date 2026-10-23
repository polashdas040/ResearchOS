from uuid import uuid4

import pytest

from packages.rag.researchos_rag.evidence_packs import (
    EvidenceItem,
    EvidencePack,
    EvidenceSource,
)
from packages.writing.researchos_writing.academic import (
    AcademicSection,
    AcademicWritingAssistant,
    WritingRequest,
)


def _evidence_pack() -> EvidencePack:
    return EvidencePack(
        query="Draft a result section",
        items=[
            EvidenceItem(
                chunk_id=uuid4(),
                content="The proposed model achieved 91.5% accuracy and 0.94 AUC.",
                source=EvidenceSource(
                    document_id=uuid4(),
                    page=5,
                    section="Results",
                    element_type="PARAGRAPH",
                ),
                retrieval_score=0.8,
                rerank_score=0.9,
            )
        ],
    )


def test_academic_writing_assistant_drafts_section_with_verified_citation() -> None:
    draft = AcademicWritingAssistant().draft_section(
        WritingRequest(
            section=AcademicSection.RESULTS,
            instruction="Summarize the model performance.",
            evidence_pack=_evidence_pack(),
        )
    )

    assert draft.section == AcademicSection.RESULTS
    assert "91.5% accuracy" in draft.content
    assert draft.citation_ids == ["E1"]
    assert draft.claims[0].citation_ids == ["E1"]
    assert draft.warnings == []


def test_academic_writing_assistant_rejects_claims_without_evidence() -> None:
    with pytest.raises(ValueError, match="evidence"):
        AcademicWritingAssistant().draft_section(
            WritingRequest(
                section=AcademicSection.INTRODUCTION,
                instruction="Claim this is the first method ever.",
                evidence_pack=EvidencePack(query="novelty", items=[]),
            )
        )


def test_academic_writing_assistant_builds_outline_without_inventing_citations() -> None:
    outline = AcademicWritingAssistant().build_outline("Mamba-based ADNI study")

    assert outline.title == "Mamba-based ADNI study"
    assert [section.section for section in outline.sections] == [
        AcademicSection.ABSTRACT,
        AcademicSection.INTRODUCTION,
        AcademicSection.METHODS,
        AcademicSection.RESULTS,
        AcademicSection.DISCUSSION,
    ]
    assert all(section.required_evidence for section in outline.sections)
