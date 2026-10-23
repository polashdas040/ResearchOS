from typing import Any, Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from apps.api.app.domain.evidence.models import Claim
from packages.agents.researchos_agents.literature import PaperRecord


class GapAnalysisError(ValueError):
    """Raised when a proposed research gap is not evidence grounded."""


class GapAnalysisRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    papers: list[PaperRecord] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    methods: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    dataset_profile: dict[str, Any] = Field(default_factory=dict)


class GapProposal(BaseModel):
    model_config = ConfigDict(frozen=True)

    description: str = Field(min_length=1)
    supporting_paper_ids: list[str] = Field(default_factory=list)
    contradicting_paper_ids: list[str] = Field(default_factory=list)
    supporting_claim_ids: list[UUID] = Field(default_factory=list)
    contradicting_claim_ids: list[UUID] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    opportunity: str = Field(min_length=1)
    data_requirements: list[str] = Field(default_factory=list)


class ResearchGap(GapProposal):
    id: UUID = Field(default_factory=uuid4)


class GapAnalysisResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    gaps: list[ResearchGap] = Field(default_factory=list)


class GapReasoner(Protocol):
    async def propose(self, request: GapAnalysisRequest) -> list[GapProposal]: ...


class GapAnalysisAgent:
    def __init__(self, reasoner: GapReasoner) -> None:
        self._reasoner = reasoner

    async def analyze(self, request: GapAnalysisRequest) -> GapAnalysisResult:
        proposals = await self._reasoner.propose(request)
        paper_ids = {paper.paper_id for paper in request.papers}
        claim_ids = {claim.id for claim in request.claims}
        gaps = [
            self._validate_proposal(proposal, paper_ids, claim_ids)
            for proposal in proposals
        ]
        return GapAnalysisResult(gaps=gaps)

    @staticmethod
    def _validate_proposal(
        proposal: GapProposal,
        paper_ids: set[str],
        claim_ids: set[UUID],
    ) -> ResearchGap:
        supporting_papers = set(proposal.supporting_paper_ids)
        contradicting_papers = set(proposal.contradicting_paper_ids)
        supporting_claims = set(proposal.supporting_claim_ids)
        contradicting_claims = set(proposal.contradicting_claim_ids)
        if supporting_papers & contradicting_papers:
            raise GapAnalysisError("Paper cannot be both supporting and contradicting")
        if supporting_claims & contradicting_claims:
            raise GapAnalysisError("Claim cannot be both supporting and contradicting")
        referenced_papers = supporting_papers | contradicting_papers
        referenced_claims = supporting_claims | contradicting_claims
        if not referenced_papers and not referenced_claims:
            raise GapAnalysisError("Research gap requires provenance")
        unknown_papers = referenced_papers - paper_ids
        if unknown_papers:
            unknown_paper = sorted(unknown_papers)[0]
            raise GapAnalysisError(f"Research gap references unknown paper: {unknown_paper}")
        unknown_claims = referenced_claims - claim_ids
        if unknown_claims:
            raise GapAnalysisError("Research gap references unknown claim")
        return ResearchGap(**proposal.model_dump())
