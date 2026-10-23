from dataclasses import dataclass

import pytest

from packages.agents.researchos_agents.autonomous_loop import (
    AutonomousResearchLoop,
    LoopStatus,
    ResearchMode,
    ResearchObservation,
    VerificationOutcome,
)


@dataclass
class FakePlanner:
    async def plan(self, goal: str) -> list[str]:
        return [f"Investigate: {goal}"]


@dataclass
class FakeScheduler:
    async def execute(self, tasks: list[str]) -> list[ResearchObservation]:
        return [
            ResearchObservation(
                task=tasks[0],
                evidence_ids=["evidence-1"],
                claim_ids=["claim-1"],
                artifact_ids=["artifact-1"],
            )
        ]


@dataclass
class FakeVerifier:
    outcome: VerificationOutcome

    async def verify(self, observations: list[ResearchObservation]) -> VerificationOutcome:
        return self.outcome


@pytest.mark.asyncio
async def test_autonomous_loop_persists_verified_artifacts_and_evidence() -> None:
    loop = AutonomousResearchLoop(
        FakePlanner(),
        FakeScheduler(),
        FakeVerifier(VerificationOutcome.VERIFIED),
    )

    result = await loop.run("Find a reproducible biomarker signal")

    assert result.status == LoopStatus.SUCCEEDED
    assert result.evidence_ids == ["evidence-1"]
    assert result.artifact_ids == ["artifact-1"]
    assert result.claim_ids == ["claim-1"]
    assert result.tasks == ["Investigate: Find a reproducible biomarker signal"]


@pytest.mark.asyncio
async def test_autonomous_loop_can_resume_and_cancel_persisted_runs() -> None:
    loop = AutonomousResearchLoop(
        FakePlanner(),
        FakeScheduler(),
        FakeVerifier(VerificationOutcome.VERIFIED),
    )
    created = await loop.start("Resume this run")
    cancelled = await loop.cancel(created.id)

    assert cancelled.status == LoopStatus.CANCELLED
    resumed = await loop.resume(created.id)
    assert resumed.status == LoopStatus.SUCCEEDED


@pytest.mark.asyncio
async def test_autonomous_loop_preserves_research_mode() -> None:
    loop = AutonomousResearchLoop(
        FakePlanner(),
        FakeScheduler(),
        FakeVerifier(VerificationOutcome.VERIFIED),
    )

    result = await loop.run("Review this paper", mode=ResearchMode.PAPER_REVIEW)

    assert result.mode == ResearchMode.PAPER_REVIEW
