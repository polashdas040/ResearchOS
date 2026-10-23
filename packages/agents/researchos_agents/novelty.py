from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from packages.agents.researchos_agents.hypothesis import Hypothesis
from packages.agents.researchos_agents.literature import PaperRecord


class NoveltyAuditError(ValueError):
    """Raised when novelty cannot be grounded in closest prior work."""


class NoveltyRisk(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class NoveltyProposal(BaseModel):
    model_config = ConfigDict(frozen=True)

    closest_paper_ids: list[str] = Field(default_factory=list)
    overlapping_contribution: str = Field(min_length=1)
    remaining_difference: str = Field(min_length=1)
    novelty_risk: NoveltyRisk
    confidence: float = Field(ge=0.0, le=1.0)


class NoveltyReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    hypothesis_id: str
    novelty_query: str
    closest_papers: list[PaperRecord]
    overlapping_contribution: str
    remaining_difference: str
    novelty_risk: NoveltyRisk
    confidence: float


class NoveltySearchProvider(Protocol):
    async def search(self, query: str, limit: int) -> list[PaperRecord]: ...


class NoveltyEvaluator(Protocol):
    async def assess(
        self,
        hypothesis: Hypothesis,
        papers: list[PaperRecord],
    ) -> NoveltyProposal: ...


class NoveltyAuditor:
    def __init__(
        self,
        provider: NoveltySearchProvider,
        evaluator: NoveltyEvaluator,
    ) -> None:
        self._provider = provider
        self._evaluator = evaluator

    async def audit(self, hypothesis: Hypothesis, limit: int = 10) -> NoveltyReport:
        if limit < 1:
            raise ValueError("limit must be at least 1")
        query = _novelty_query(hypothesis)
        papers = await self._provider.search(query, limit)
        if not papers:
            raise NoveltyAuditError("Novelty report requires closest-work evidence")
        proposal = await self._evaluator.assess(hypothesis, papers)
        if not proposal.closest_paper_ids:
            raise NoveltyAuditError("Novelty report requires closest-work evidence")
        if len(set(proposal.closest_paper_ids)) != len(proposal.closest_paper_ids):
            raise NoveltyAuditError("Novelty report contains duplicate closest papers")
        papers_by_id = {paper.paper_id: paper for paper in papers}
        unknown_paper = next(
            (paper_id for paper_id in proposal.closest_paper_ids if paper_id not in papers_by_id),
            None,
        )
        if unknown_paper is not None:
            raise NoveltyAuditError(
                f"Novelty report references unknown closest paper: {unknown_paper}"
            )
        return NoveltyReport(
            hypothesis_id=str(hypothesis.id),
            novelty_query=query,
            closest_papers=[papers_by_id[paper_id] for paper_id in proposal.closest_paper_ids],
            overlapping_contribution=proposal.overlapping_contribution,
            remaining_difference=proposal.remaining_difference,
            novelty_risk=proposal.novelty_risk,
            confidence=proposal.confidence,
        )


def _novelty_query(hypothesis: Hypothesis) -> str:
    return f"{hypothesis.statement} closest prior work method comparison"
