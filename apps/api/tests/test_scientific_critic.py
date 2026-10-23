from dataclasses import dataclass

import pytest

from packages.agents.researchos_agents.feasibility import FeasibilityDecision, FeasibilityResult
from packages.agents.researchos_agents.hypothesis import Hypothesis
from packages.agents.researchos_agents.scientific_critic import (
    CriticCategory,
    CriticDecision,
    CriticIssue,
    CriticRequest,
    CriticSeverity,
    ScientificCritic,
)


@dataclass
class FakeReviewer:
    issues: list[CriticIssue]
    received_request: CriticRequest | None = None

    async def review(self, request: CriticRequest) -> list[CriticIssue]:
        self.received_request = request
        return self.issues


def hypothesis() -> Hypothesis:
    return Hypothesis(
        statement="A calibrated model improves prediction.",
        rationale="A structured rationale.",
        required_data=["outcome"],
        supporting_gap_ids=[],
        falsification_test="The model does not beat the baseline.",
        generation_strategy="calibration",
    )


@pytest.mark.asyncio
async def test_critical_issue_rejects_hypothesis_and_preserves_category() -> None:
    reviewer = FakeReviewer(
        issues=[
            CriticIssue(
                category=CriticCategory.LEAKAGE,
                severity=CriticSeverity.CRITICAL,
                finding="The proposed split leaks subject identity across partitions.",
                recommendation="Split by subject before feature construction.",
            )
        ]
    )
    result = await ScientificCritic(reviewer).review(
        CriticRequest(hypothesis=hypothesis(), evidence_summary=["Subject-level split"])
    )

    assert result.decision == CriticDecision.REJECT
    assert result.issues[0].category == CriticCategory.LEAKAGE
    assert result.issues[0].severity == CriticSeverity.CRITICAL


@pytest.mark.asyncio
async def test_major_issue_requires_revision_and_structured_context_is_forwarded() -> None:
    reviewer = FakeReviewer(
        issues=[
            CriticIssue(
                category=CriticCategory.STATISTICS,
                severity=CriticSeverity.MAJOR,
                finding="Uncertainty is not reported.",
                recommendation="Report confidence intervals.",
            )
        ]
    )
    request = CriticRequest(
        hypothesis=hypothesis(),
        evidence_summary=["Three supporting studies"],
        experiment_summary={"metric": "AUROC"},
    )

    result = await ScientificCritic(reviewer).review(request)

    assert result.decision == CriticDecision.REVISE
    assert reviewer.received_request == request
    assert not hasattr(reviewer.received_request, "internal_generation_trace")


@pytest.mark.asyncio
async def test_minor_issues_are_recorded_without_rejection() -> None:
    result = await ScientificCritic(
        FakeReviewer(
            issues=[
                CriticIssue(
                    category=CriticCategory.REPRODUCIBILITY,
                    severity=CriticSeverity.MINOR,
                    finding="The random seed is not stated.",
                    recommendation="Record the seed in the experiment specification.",
                )
            ]
        )
    ).review(CriticRequest(hypothesis=hypothesis()))

    assert result.decision == CriticDecision.ACCEPT
    assert result.issues[0].category == CriticCategory.REPRODUCIBILITY


@pytest.mark.asyncio
async def test_feasibility_failure_is_a_critical_review_issue() -> None:
    result = await ScientificCritic(FakeReviewer(issues=[])).review(
        CriticRequest(
            hypothesis=hypothesis(),
            feasibility_result=FeasibilityResult(
                decision=FeasibilityDecision.FAIL,
                reasons=["Required imaging modality is unavailable."],
                recommendations=["Provide imaging data."],
            ),
        )
    )

    assert result.decision == CriticDecision.REJECT
    assert result.issues[0].category == CriticCategory.METHODOLOGY
    assert result.issues[0].severity == CriticSeverity.CRITICAL
