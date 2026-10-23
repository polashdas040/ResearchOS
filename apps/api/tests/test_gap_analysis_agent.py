from dataclasses import dataclass
from uuid import uuid4

import pytest

from apps.api.app.domain.evidence.models import Claim, ClaimStatus, ClaimType
from packages.agents.researchos_agents.gap_analysis import (
    GapAnalysisAgent,
    GapAnalysisError,
    GapAnalysisRequest,
    GapProposal,
)
from packages.agents.researchos_agents.literature import PaperRecord


@dataclass
class FakeGapReasoner:
    proposals: list[GapProposal]
    received_request: GapAnalysisRequest | None = None

    async def propose(self, request: GapAnalysisRequest) -> list[GapProposal]:
        self.received_request = request
        return self.proposals


def _paper(paper_id: str, title: str) -> PaperRecord:
    return PaperRecord(paper_id=paper_id, title=title, authors=[], publication_year=2024)


@pytest.mark.asyncio
async def test_gap_analysis_returns_structured_provenance_backed_gaps() -> None:
    claim = Claim(
        id=uuid4(),
        statement="Most studies use short follow-up periods.",
        claim_type=ClaimType.METHODOLOGICAL,
        status=ClaimStatus.PROPOSED,
    )
    reasoner = FakeGapReasoner(
        proposals=[
            GapProposal(
                description="Long-term follow-up remains under-studied.",
                supporting_paper_ids=["paper-1"],
                supporting_claim_ids=[claim.id],
                confidence=0.82,
                opportunity="Evaluate the method over longer follow-up periods.",
                data_requirements=["longitudinal outcomes"],
            )
        ]
    )
    agent = GapAnalysisAgent(reasoner)

    result = await agent.analyze(
        GapAnalysisRequest(
            papers=[_paper("paper-1", "A short follow-up study")],
            claims=[claim],
            methods=["observational cohort"],
            limitations=["short follow-up"],
            dataset_profile={"follow_up_months": 12},
        )
    )

    assert len(result.gaps) == 1
    assert result.gaps[0].supporting_paper_ids == ["paper-1"]
    assert result.gaps[0].supporting_claim_ids == [claim.id]
    assert result.gaps[0].opportunity
    assert reasoner.received_request is not None
    assert reasoner.received_request.dataset_profile["follow_up_months"] == 12


@pytest.mark.asyncio
async def test_gap_analysis_rejects_unsupported_gap_proposals() -> None:
    reasoner = FakeGapReasoner(
        proposals=[
            GapProposal(
                description="This is a novel research direction.",
                supporting_paper_ids=[],
                confidence=0.99,
                opportunity="Build a new method.",
                data_requirements=[],
            )
        ]
    )
    agent = GapAnalysisAgent(reasoner)

    with pytest.raises(GapAnalysisError, match="provenance"):
        await agent.analyze(
            GapAnalysisRequest(papers=[_paper("paper-1", "Existing work")])
        )


@pytest.mark.asyncio
async def test_gap_analysis_rejects_unknown_provenance_ids() -> None:
    reasoner = FakeGapReasoner(
        proposals=[
            GapProposal(
                description="A missing comparison is reported.",
                supporting_paper_ids=["missing-paper"],
                confidence=0.5,
                opportunity="Compare methods.",
                data_requirements=["benchmark dataset"],
            )
        ]
    )
    agent = GapAnalysisAgent(reasoner)

    with pytest.raises(GapAnalysisError, match="unknown paper"):
        await agent.analyze(
            GapAnalysisRequest(papers=[_paper("paper-1", "Existing work")])
        )


@pytest.mark.asyncio
async def test_gap_analysis_rejects_conflicting_provenance_roles() -> None:
    reasoner = FakeGapReasoner(
        proposals=[
            GapProposal(
                description="The evidence has an unresolved limitation.",
                supporting_paper_ids=["paper-1"],
                contradicting_paper_ids=["paper-1"],
                confidence=0.5,
                opportunity="Compare the reported methods.",
            )
        ]
    )

    with pytest.raises(GapAnalysisError, match="both supporting and contradicting"):
        await GapAnalysisAgent(reasoner).analyze(
            GapAnalysisRequest(papers=[_paper("paper-1", "Existing work")])
        )
