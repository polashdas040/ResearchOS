from enum import StrEnum
from typing import Any, Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from apps.api.app.domain.evidence.models import Claim
from packages.agents.researchos_agents.gap_analysis import ResearchGap


class HypothesisGenerationError(ValueError):
    """Raised when a proposed hypothesis is not structured or evidence grounded."""


class HypothesisStatus(StrEnum):
    PROPOSED = "PROPOSED"
    TESTED = "TESTED"
    SUPPORTED = "SUPPORTED"
    REJECTED = "REJECTED"


class HypothesisGenerationRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    claims: list[Claim] = Field(default_factory=list)
    gaps: list[ResearchGap] = Field(default_factory=list)
    dataset_profile: dict[str, Any] = Field(default_factory=dict)


class HypothesisProposal(BaseModel):
    model_config = ConfigDict(frozen=True)

    statement: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    mechanism: str | None = None
    required_data: list[str] = Field(default_factory=list)
    supporting_claim_ids: list[UUID] = Field(default_factory=list)
    supporting_gap_ids: list[UUID] = Field(default_factory=list)
    falsification_test: str = Field(min_length=1)
    generation_strategy: str = Field(min_length=1)


class Hypothesis(HypothesisProposal):
    id: UUID = Field(default_factory=uuid4)
    status: HypothesisStatus = HypothesisStatus.PROPOSED


class HypothesisGenerationResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    hypotheses: list[Hypothesis] = Field(default_factory=list)


class HypothesisReasoner(Protocol):
    async def propose(
        self,
        request: HypothesisGenerationRequest,
    ) -> list[HypothesisProposal]: ...


class HypothesisGenerator:
    def __init__(self, reasoner: HypothesisReasoner) -> None:
        self._reasoner = reasoner

    async def generate(
        self,
        request: HypothesisGenerationRequest,
    ) -> HypothesisGenerationResult:
        proposals = await self._reasoner.propose(request)
        claim_ids = {claim.id for claim in request.claims}
        gap_ids = {gap.id for gap in request.gaps}
        hypotheses: list[Hypothesis] = []
        statements: set[str] = set()
        for proposal in proposals:
            hypothesis = self._validate_proposal(proposal, claim_ids, gap_ids)
            statement_key = " ".join(hypothesis.statement.split()).casefold()
            if statement_key in statements:
                raise HypothesisGenerationError("Hypothesis statements must be diverse")
            statements.add(statement_key)
            hypotheses.append(hypothesis)
        return HypothesisGenerationResult(hypotheses=hypotheses)

    @staticmethod
    def _validate_proposal(
        proposal: HypothesisProposal,
        claim_ids: set[UUID],
        gap_ids: set[UUID],
    ) -> Hypothesis:
        if not proposal.supporting_claim_ids and not proposal.supporting_gap_ids:
            raise HypothesisGenerationError("Hypothesis requires evidence references")
        supporting_claim_ids = set(proposal.supporting_claim_ids)
        supporting_gap_ids = set(proposal.supporting_gap_ids)
        if len(supporting_claim_ids) != len(proposal.supporting_claim_ids):
            raise HypothesisGenerationError("Hypothesis contains duplicate claim references")
        if len(supporting_gap_ids) != len(proposal.supporting_gap_ids):
            raise HypothesisGenerationError("Hypothesis contains duplicate gap references")
        unknown_claims = supporting_claim_ids - claim_ids
        if unknown_claims:
            raise HypothesisGenerationError("Hypothesis references unknown claim")
        unknown_gaps = supporting_gap_ids - gap_ids
        if unknown_gaps:
            raise HypothesisGenerationError("Hypothesis references unknown gap")
        return Hypothesis(**proposal.model_dump())
