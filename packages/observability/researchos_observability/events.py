from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class EventType(StrEnum):
    RESEARCH_RUN_STARTED = "research_run.started"
    RESEARCH_RUN_COMPLETED = "research_run.completed"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TOOL_CALLED = "tool.called"
    TOOL_COMPLETED = "tool.completed"
    AGENT_COMPLETED = "agent.completed"
    CLAIM_CREATED = "claim.created"
    EXPERIMENT_COMPLETED = "experiment.completed"
    VERIFICATION_FAILED = "verification.failed"


class ObservabilityEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    event_type: EventType
    trace_id: UUID | None
    research_run_id: UUID | None = None
    task_id: UUID | None = None
    tool_name: str | None = None
    latency_ms: float = Field(default=0.0, ge=0.0)
    tokens: int = Field(default=0, ge=0)
    cost: float = Field(default=0.0, ge=0.0)
    retry_count: int = Field(default=0, ge=0)
    sequence: int = Field(default=0, ge=0)
    metadata: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ObservabilityStore:
    def __init__(self) -> None:
        self._events: list[ObservabilityEvent] = []
        self._next_sequence = 1

    async def record(self, event: ObservabilityEvent) -> ObservabilityEvent:
        if event.trace_id is None:
            raise ValueError("observability event requires trace correlation")
        sequenced = event.model_copy(update={"sequence": self._next_sequence})
        self._next_sequence += 1
        self._events.append(sequenced)
        return sequenced

    async def trace(self, trace_id: UUID) -> list[ObservabilityEvent]:
        events = [event for event in self._events if event.trace_id == trace_id]
        if not events:
            raise KeyError(f"observability trace not found: {trace_id}")
        return sorted(events, key=lambda event: event.sequence)
