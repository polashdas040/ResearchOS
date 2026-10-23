from dataclasses import dataclass

import pytest

from packages.agents.researchos_agents.hypothesis import Hypothesis
from packages.agents.researchos_agents.literature import PaperRecord
from packages.agents.researchos_agents.novelty import (
    NoveltyAuditError,
    NoveltyAuditor,
    NoveltyProposal,
    NoveltyRisk,
)


@dataclass
class FakeNoveltyProvider:
    papers: list[PaperRecord]
    queries: list[str]

    async def search(self, query: str, limit: int) -> list[PaperRecord]:
        self.queries.append(query)
        return self.papers[:limit]


@dataclass
class FakeNoveltyEvaluator:
    proposal: NoveltyProposal

    async def assess(
        self,
        hypothesis: Hypothesis,
        papers: list[PaperRecord],
    ) -> NoveltyProposal:
        assert hypothesis.statement
        assert papers
        return self.proposal


def _hypothesis() -> Hypothesis:
    return Hypothesis(
        statement="Longer follow-up improves prediction of cognitive decline.",
        rationale="Short follow-up is a documented research gap.",
        required_data=["longitudinal outcomes"],
        supporting_gap_ids=[],
        supporting_claim_ids=[],
        falsification_test="Compare performance with and without longer follow-up.",
        generation_strategy="temporal_extension",
    )


def _paper(paper_id: str) -> PaperRecord:
    return PaperRecord(
        paper_id=paper_id,
        title=f"Prior work {paper_id}",
        authors=["A. Researcher"],
        abstract="Prior method description.",
        publication_year=2022,
        relevance_score=0.9,
    )


@pytest.mark.asyncio
async def test_novelty_auditor_returns_evidence_backed_report() -> None:
    provider = FakeNoveltyProvider(papers=[_paper("paper-1")], queries=[])
    evaluator = FakeNoveltyEvaluator(
        proposal=NoveltyProposal(
            closest_paper_ids=["paper-1"],
            overlapping_contribution="Both use longitudinal prediction.",
            remaining_difference="The proposed work evaluates longer follow-up.",
            novelty_risk=NoveltyRisk.MEDIUM,
            confidence=0.76,
        )
    )
    auditor = NoveltyAuditor(provider, evaluator)

    report = await auditor.audit(_hypothesis(), limit=5)

    assert provider.queries[0].startswith("Longer follow-up improves prediction")
    assert report.closest_papers[0].paper_id == "paper-1"
    assert report.remaining_difference
    assert report.novelty_risk == "MEDIUM"
    assert report.confidence == 0.76


@pytest.mark.asyncio
async def test_novelty_auditor_rejects_report_without_closest_work() -> None:
    auditor = NoveltyAuditor(
        FakeNoveltyProvider(papers=[_paper("paper-1")], queries=[]),
        FakeNoveltyEvaluator(
            proposal=NoveltyProposal(
                closest_paper_ids=[],
                overlapping_contribution="None identified.",
                remaining_difference="Unknown.",
                novelty_risk=NoveltyRisk.HIGH,
                confidence=0.2,
            )
        ),
    )

    with pytest.raises(NoveltyAuditError, match="closest-work evidence"):
        await auditor.audit(_hypothesis())


@pytest.mark.asyncio
async def test_novelty_auditor_rejects_unknown_closest_paper() -> None:
    auditor = NoveltyAuditor(
        FakeNoveltyProvider(papers=[_paper("paper-1")], queries=[]),
        FakeNoveltyEvaluator(
            proposal=NoveltyProposal(
                closest_paper_ids=["missing-paper"],
                overlapping_contribution="Unknown.",
                remaining_difference="Unknown.",
                novelty_risk=NoveltyRisk.HIGH,
                confidence=0.1,
            )
        ),
    )

    with pytest.raises(NoveltyAuditError, match="unknown closest paper"):
        await auditor.audit(_hypothesis())


@pytest.mark.asyncio
async def test_novelty_auditor_rejects_duplicate_closest_papers() -> None:
    auditor = NoveltyAuditor(
        FakeNoveltyProvider(papers=[_paper("paper-1")], queries=[]),
        FakeNoveltyEvaluator(
            proposal=NoveltyProposal(
                closest_paper_ids=["paper-1", "paper-1"],
                overlapping_contribution="Both use longitudinal prediction.",
                remaining_difference="The proposed work extends follow-up.",
                novelty_risk=NoveltyRisk.MEDIUM,
                confidence=0.5,
            )
        ),
    )

    with pytest.raises(NoveltyAuditError, match="duplicate"):
        await auditor.audit(_hypothesis())


@pytest.mark.asyncio
async def test_novelty_auditor_rejects_empty_literature_search_before_assessment() -> None:
    auditor = NoveltyAuditor(
        FakeNoveltyProvider(papers=[], queries=[]),
        FakeNoveltyEvaluator(
            proposal=NoveltyProposal(
                closest_paper_ids=["paper-1"],
                overlapping_contribution="Unknown.",
                remaining_difference="Unknown.",
                novelty_risk=NoveltyRisk.HIGH,
                confidence=0.1,
            )
        ),
    )

    with pytest.raises(NoveltyAuditError, match="closest-work evidence"):
        await auditor.audit(_hypothesis())
