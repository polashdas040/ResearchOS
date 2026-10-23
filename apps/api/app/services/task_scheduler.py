from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from apps.api.app.services.dynamic_planner import ProposedTask, TaskGraph


class TaskSchedulerError(Exception):
    """Raised when a task graph cannot be scheduled safely."""


class TaskStatus(StrEnum):
    PENDING = "PENDING"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING_USER = "WAITING_USER"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    SKIPPED = "SKIPPED"


class TaskExecutionState(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: TaskStatus
    retry_count: int = Field(default=0, ge=0)
    actual_cost: float = Field(default=0.0, ge=0.0)


class SchedulerLimits(BaseModel):
    model_config = ConfigDict(frozen=True)

    max_concurrent_tasks: int = Field(gt=0)
    remaining_budget: float = Field(ge=0.0)
    per_capability_limits: dict[str, int] = Field(default_factory=dict)


class SchedulingDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    to_dispatch: list[ProposedTask] = Field(default_factory=list)
    ready_task_ids: list[UUID] = Field(default_factory=list)
    waiting_task_ids: list[UUID] = Field(default_factory=list)
    running_task_ids: list[UUID] = Field(default_factory=list)
    budget_blocked_task_ids: list[UUID] = Field(default_factory=list)
    permanent_failure_task_ids: list[UUID] = Field(default_factory=list)
    skipped_task_ids: list[UUID] = Field(default_factory=list)
    cancelled_task_ids: list[UUID] = Field(default_factory=list)
    consumed_dispatch_budget: float = 0.0


class TaskScheduler:
    def schedule(
        self,
        graph: TaskGraph,
        states: dict[UUID, TaskExecutionState],
        limits: SchedulerLimits,
    ) -> SchedulingDecision:
        graph.validate_graph()
        tasks_by_id = {task.id: task for task in graph.tasks}
        unknown_task_ids = [task_id for task_id in states if task_id not in tasks_by_id]
        if unknown_task_ids:
            raise TaskSchedulerError(f"Unknown task state: {unknown_task_ids[0]}")

        running_task_ids = [
            task.id
            for task in graph.tasks
            if states.get(task.id, TaskExecutionState(status=TaskStatus.PENDING)).status
            == TaskStatus.RUNNING
        ]
        cancelled_task_ids = [
            task.id
            for task in graph.tasks
            if states.get(task.id, TaskExecutionState(status=TaskStatus.PENDING)).status
            == TaskStatus.CANCELLED
        ]
        permanent_failure_task_ids = [
            task.id for task in graph.tasks if _is_permanent_failure(task, states.get(task.id))
        ]
        blocked_dependency_ids = set(cancelled_task_ids) | set(permanent_failure_task_ids)
        skipped_task_ids = _collect_skipped_task_ids(graph.tasks, blocked_dependency_ids, states)

        ready_tasks: list[ProposedTask] = []
        waiting_task_ids: list[UUID] = []
        budget_blocked_task_ids: list[UUID] = []
        available_slots = max(0, limits.max_concurrent_tasks - len(running_task_ids))
        remaining_budget = limits.remaining_budget
        capability_counts = _running_capability_counts(graph.tasks, states)

        for task in graph.tasks:
            state = states.get(task.id, TaskExecutionState(status=TaskStatus.PENDING))
            if not _can_be_considered(task, state, skipped_task_ids):
                continue
            if not _dependencies_succeeded(task, states):
                waiting_task_ids.append(task.id)
                continue
            ready_tasks.append(task)

        to_dispatch: list[ProposedTask] = []
        for task in ready_tasks:
            capability = task.assigned_capability.lower()
            capability_limit = limits.per_capability_limits.get(capability)
            if (
                capability_limit is not None
                and capability_counts.get(capability, 0) >= capability_limit
            ):
                continue
            if task.estimated_cost > remaining_budget:
                budget_blocked_task_ids.append(task.id)
                continue
            if len(to_dispatch) >= available_slots:
                continue
            to_dispatch.append(task)
            remaining_budget -= task.estimated_cost
            capability_counts[capability] = capability_counts.get(capability, 0) + 1

        return SchedulingDecision(
            to_dispatch=to_dispatch,
            ready_task_ids=[task.id for task in ready_tasks],
            waiting_task_ids=waiting_task_ids,
            running_task_ids=running_task_ids,
            budget_blocked_task_ids=budget_blocked_task_ids,
            permanent_failure_task_ids=permanent_failure_task_ids,
            skipped_task_ids=skipped_task_ids,
            cancelled_task_ids=cancelled_task_ids,
            consumed_dispatch_budget=sum(task.estimated_cost for task in to_dispatch),
        )


def _can_be_considered(
    task: ProposedTask,
    state: TaskExecutionState,
    skipped_task_ids: list[UUID],
) -> bool:
    if task.id in skipped_task_ids:
        return False
    if state.status in {
        TaskStatus.RUNNING,
        TaskStatus.WAITING_USER,
        TaskStatus.SUCCEEDED,
        TaskStatus.CANCELLED,
        TaskStatus.SKIPPED,
    }:
        return False
    if state.status == TaskStatus.FAILED and state.retry_count >= task.max_retries:
        return False
    return True


def _dependencies_succeeded(task: ProposedTask, states: dict[UUID, TaskExecutionState]) -> bool:
    return all(
        states.get(dependency_id, TaskExecutionState(status=TaskStatus.PENDING)).status
        == TaskStatus.SUCCEEDED
        for dependency_id in task.dependencies
    )


def _is_permanent_failure(
    task: ProposedTask,
    state: TaskExecutionState | None,
) -> bool:
    return (
        state is not None
        and state.status == TaskStatus.FAILED
        and state.retry_count >= task.max_retries
    )


def _collect_skipped_task_ids(
    tasks: list[ProposedTask],
    blocked_dependency_ids: set[UUID],
    states: dict[UUID, TaskExecutionState],
) -> list[UUID]:
    skipped: list[UUID] = []
    skipped_ids: set[UUID] = set()
    changed = True
    while changed:
        changed = False
        for task in tasks:
            state = states.get(task.id)
            if state is not None and state.status in {
                TaskStatus.SUCCEEDED,
                TaskStatus.CANCELLED,
                TaskStatus.SKIPPED,
            }:
                continue
            dependency_ids = set(task.dependencies)
            if task.id not in skipped_ids and dependency_ids & (
                blocked_dependency_ids | skipped_ids
            ):
                skipped.append(task.id)
                skipped_ids.add(task.id)
                changed = True
    return skipped


def _running_capability_counts(
    tasks: list[ProposedTask],
    states: dict[UUID, TaskExecutionState],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for task in tasks:
        state = states.get(task.id)
        if state is not None and state.status == TaskStatus.RUNNING:
            capability = task.assigned_capability.lower()
            counts[capability] = counts.get(capability, 0) + 1
    return counts
