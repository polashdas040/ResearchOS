from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from packages.rag.researchos_rag.evidence_packs import EvidencePack, EvidenceSource


class CitationValidationError(ValueError):
    pass


class Citation(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    chunk_id: UUID
    source: EvidenceSource


class SupportedClaim(BaseModel):
    model_config = ConfigDict(frozen=True)

    statement: str
    citation_ids: list[str] = Field(default_factory=list)


class CitationFirstAnswer(BaseModel):
    model_config = ConfigDict(frozen=True)

    answer: str
    claims: list[SupportedClaim] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)


class CitationFirstAnswerComposer:
    def compose(self, evidence_pack: EvidencePack) -> CitationFirstAnswer:
        if not evidence_pack.items:
            return CitationFirstAnswer(answer="Evidence unavailable for this question.")

        citations = [
            Citation(id=f"E{index}", chunk_id=item.chunk_id, source=item.source)
            for index, item in enumerate(evidence_pack.items, start=1)
        ]
        claims = [
            SupportedClaim(statement=item.content, citation_ids=[citation.id])
            for item, citation in zip(evidence_pack.items, citations, strict=True)
        ]
        answer = " ".join(
            f"{claim.statement} [{claim.citation_ids[0]}]" for claim in claims
        )
        composed = CitationFirstAnswer(answer=answer, claims=claims, citations=citations)
        self.validate(composed, evidence_pack)
        return composed

    def validate(
        self,
        answer: CitationFirstAnswer,
        evidence_pack: EvidencePack,
    ) -> None:
        citations_by_id = {citation.id: citation for citation in answer.citations}
        evidence_by_chunk_id = {item.chunk_id: item for item in evidence_pack.items}

        for claim in answer.claims:
            if not claim.citation_ids:
                raise CitationValidationError("Claim has no citation.")
            for citation_id in claim.citation_ids:
                citation = citations_by_id.get(citation_id)
                if citation is None:
                    raise CitationValidationError(f"Unknown citation id: {citation_id}")
                evidence_item = evidence_by_chunk_id.get(citation.chunk_id)
                if evidence_item is None:
                    raise CitationValidationError(
                        f"Citation {citation_id} does not point to evidence."
                    )
                if claim.statement != evidence_item.content:
                    raise CitationValidationError(
                        f"Claim is not supported by citation {citation_id}."
                    )
