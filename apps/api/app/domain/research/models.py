from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class ResearchRunStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    INTERRUPTED = "INTERRUPTED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class RuntimeNode(StrEnum):
    START = "START"
    INTENT = "INTENT"
    CONTEXT_COMPILER = "CONTEXT_COMPILER"
    PLANNER = "PLANNER"
    TASK_SCHEDULER = "TASK_SCHEDULER"
    ANSWER_COMPOSER = "ANSWER_COMPOSER"
    MEMORY_UPDATE = "MEMORY_UPDATE"
    END = "END"


class ResearchState(BaseModel):
    model_config = ConfigDict(frozen=True)

    research_run_id: UUID
    user_id: UUID
    project_id: UUID
    goal: str = Field(min_length=1, max_length=20_000)
    constraint_ids: list[UUID] = Field(default_factory=list)
    open_question_ids: list[UUID] = Field(default_factory=list)
    claim_ids: list[UUID] = Field(default_factory=list)
    evidence_ids: list[UUID] = Field(default_factory=list)
    hypothesis_ids: list[UUID] = Field(default_factory=list)
    experiment_ids: list[UUID] = Field(default_factory=list)
    artifact_ids: list[UUID] = Field(default_factory=list)
    task_ids: list[UUID] = Field(default_factory=list)
    decision_ids: list[UUID] = Field(default_factory=list)


class ResearchCheckpoint(BaseModel):
    model_config = ConfigDict(frozen=True)

    node: RuntimeNode
    sequence: int
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ResearchRun(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    organization_id: UUID
    user_id: UUID
    project_id: UUID
    thread_id: str
    status: ResearchRunStatus
    state: ResearchState
    checkpoint: ResearchCheckpoint
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
