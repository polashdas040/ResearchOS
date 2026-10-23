from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class LoopStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    INTERRUPTED = "INTERRUPTED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class VerificationOutcome(StrEnum):
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    UNSUPPORTED = "UNSUPPORTED"
    CONTRADICTED = "CONTRADICTED"


class ResearchMode(StrEnum):
    CHAT = "CHAT"
    DOCUMENT_QA = "DOCUMENT_QA"
    DATA_ANALYSIS = "DATA_ANALYSIS"
    LITERATURE_REVIEW = "LITERATURE_REVIEW"
    IDEA_DISCOVERY = "IDEA_DISCOVERY"
    DEEP_RESEARCH = "DEEP_RESEARCH"
    EXPERIMENT = "EXPERIMENT"
    REPRODUCTION = "REPRODUCTION"
    PAPER_REVIEW = "PAPER_REVIEW"


class ResearchObservation(BaseModel):
    model_config = ConfigDict(frozen=True)

    task: str = Field(min_length=1)
    evidence_ids: list[str] = Field(default_factory=list)
    claim_ids: list[str] = Field(default_factory=list)
    artifact_ids: list[str] = Field(default_factory=list)


class ResearchLoopRun(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    goal: str = Field(min_length=1)
    mode: ResearchMode = ResearchMode.DEEP_RESEARCH
    status: LoopStatus
    tasks: list[str] = Field(default_factory=list)
    observations: list[ResearchObservation] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    claim_ids: list[str] = Field(default_factory=list)
    artifact_ids: list[str] = Field(default_factory=list)
    verification: VerificationOutcome | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ResearchPlanner(Protocol):
    async def plan(self, goal: str) -> list[str]: ...


class ResearchScheduler(Protocol):
    async def execute(self, tasks: list[str]) -> list[ResearchObservation]: ...


class ResearchVerifier(Protocol):
    async def verify(self, observations: list[ResearchObservation]) -> VerificationOutcome: ...


class AutonomousResearchLoop:
    def __init__(
        self,
        planner: ResearchPlanner,
        scheduler: ResearchScheduler,
        verifier: ResearchVerifier,
    ) -> None:
        self._planner = planner
        self._scheduler = scheduler
        self._verifier = verifier
        self._runs: dict[UUID, ResearchLoopRun] = {}

    async def start(
        self,
        goal: str,
        mode: ResearchMode = ResearchMode.DEEP_RESEARCH,
    ) -> ResearchLoopRun:
        run = ResearchLoopRun(goal=goal, mode=mode, status=LoopStatus.PENDING)
        self._runs[run.id] = run
        return run

    async def run(
        self,
        goal: str,
        mode: ResearchMode = ResearchMode.DEEP_RESEARCH,
    ) -> ResearchLoopRun:
        run = await self.start(goal, mode=mode)
        return await self.resume(run.id)

    async def resume(self, run_id: UUID) -> ResearchLoopRun:
        run = self._get(run_id)
        if run.status == LoopStatus.CANCELLED:
            run = run.model_copy(update={"status": LoopStatus.PENDING})
        tasks = run.tasks or await self._planner.plan(run.goal)
        running = run.model_copy(update={"status": LoopStatus.RUNNING, "tasks": tasks})
        self._runs[run_id] = running
        observations = await self._scheduler.execute(tasks)
        verification = await self._verifier.verify(observations)
        completed = running.model_copy(
            update={
                "status": (
                    LoopStatus.SUCCEEDED
                    if verification == VerificationOutcome.VERIFIED
                    else LoopStatus.FAILED
                ),
                "observations": observations,
                "evidence_ids": _unique_ids(observations, "evidence_ids"),
                "claim_ids": _unique_ids(observations, "claim_ids"),
                "artifact_ids": _unique_ids(observations, "artifact_ids"),
                "verification": verification,
                "updated_at": datetime.now(UTC),
            }
        )
        self._runs[run_id] = completed
        return completed

    async def cancel(self, run_id: UUID) -> ResearchLoopRun:
        run = self._get(run_id)
        cancelled = run.model_copy(
            update={"status": LoopStatus.CANCELLED, "updated_at": datetime.now(UTC)}
        )
        self._runs[run_id] = cancelled
        return cancelled

    def _get(self, run_id: UUID) -> ResearchLoopRun:
        try:
            return self._runs[run_id]
        except KeyError as exc:
            raise KeyError(f"Research run not found: {run_id}") from exc


def _unique_ids(observations: list[ResearchObservation], field: str) -> list[str]:
    values: list[str] = []
    for observation in observations:
        for value in getattr(observation, field):
            if value not in values:
                values.append(value)
    return values
