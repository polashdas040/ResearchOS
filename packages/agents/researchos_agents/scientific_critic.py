from enum import StrEnum
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field

from packages.agents.researchos_agents.feasibility import FeasibilityDecision, FeasibilityResult
from packages.agents.researchos_agents.hypothesis import Hypothesis
from packages.agents.researchos_agents.novelty import NoveltyReport


class CriticCategory(StrEnum):
    NOVELTY = "NOVELTY"
    SCIENTIFIC_LOGIC = "SCIENTIFIC_LOGIC"
    METHODOLOGY = "METHODOLOGY"
    LEAKAGE = "LEAKAGE"
    EVALUATION = "EVALUATION"
    BASELINE = "BASELINE"
    STATISTICS = "STATISTICS"
    OVERCLAIMING = "OVERCLAIMING"
    REPRODUCIBILITY = "REPRODUCIBILITY"


class CriticSeverity(StrEnum):
    INFO = "INFO"
    MINOR = "MINOR"
    MAJOR = "MAJOR"
    CRITICAL = "CRITICAL"


class CriticDecision(StrEnum):
    ACCEPT = "ACCEPT"
    REVISE = "REVISE"
    REJECT = "REJECT"


class CriticIssue(BaseModel):
    model_config = ConfigDict(frozen=True)

    category: CriticCategory
    severity: CriticSeverity
    finding: str = Field(min_length=1)
    recommendation: str = Field(min_length=1)


class CriticRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    hypothesis: Hypothesis
    evidence_summary: list[str] = Field(default_factory=list)
    novelty_report: NoveltyReport | None = None
    feasibility_result: FeasibilityResult | None = None
    experiment_summary: dict[str, Any] = Field(default_factory=dict)


class CriticResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    decision: CriticDecision
    issues: list[CriticIssue] = Field(default_factory=list)


class ScientificReviewer(Protocol):
    async def review(self, request: CriticRequest) -> list[CriticIssue]: ...


class ScientificCritic:
    def __init__(self, reviewer: ScientificReviewer) -> None:
        self._reviewer = reviewer

    async def review(self, request: CriticRequest) -> CriticResult:
        reviewer_issues = await self._reviewer.review(request)
        issues = [*_feasibility_issues(request.feasibility_result), *reviewer_issues]
        decision = _decision_for(issues)
        return CriticResult(decision=decision, issues=issues)


def _decision_for(issues: list[CriticIssue]) -> CriticDecision:
    severities = {issue.severity for issue in issues}
    if CriticSeverity.CRITICAL in severities:
        return CriticDecision.REJECT
    if CriticSeverity.MAJOR in severities:
        return CriticDecision.REVISE
    return CriticDecision.ACCEPT


def _feasibility_issues(result: FeasibilityResult | None) -> list[CriticIssue]:
    if result is None or result.decision != FeasibilityDecision.FAIL:
        return []
    finding = result.reasons[0] if result.reasons else "The feasibility assessment failed."
    recommendation = (
        result.recommendations[0]
        if result.recommendations
        else "Resolve the feasibility blockers before advancing the hypothesis."
    )
    return [
        CriticIssue(
            category=CriticCategory.METHODOLOGY,
            severity=CriticSeverity.CRITICAL,
            finding=finding,
            recommendation=recommendation,
        )
    ]
