from uuid import UUID, uuid4

import pytest

from apps.api.app.services.dynamic_planner import ProposedTask, TaskGraph
from apps.api.app.services.task_scheduler import (
    SchedulerLimits,
    TaskExecutionState,
    TaskScheduler,
    TaskSchedulerError,
    TaskStatus,
)


def _task(
    task_type: str,
    capability: str = "literature",
    dependencies: list[UUID] | None = None,
    estimated_cost: float = 1.0,
    max_retries: int = 1,
) -> ProposedTask:
    return ProposedTask(
        task_type=task_type,
        objective=f"Run {task_type}",
        assigned_capability=capability,
        dependencies=dependencies or [],
        estimated_cost=estimated_cost,
        max_retries=max_retries,
    )


def test_independent_tasks_parallelize_with_global_limit() -> None:
    first = _task("literature_search")
    second = _task("dataset_profile", capability="dataset")
    third = _task("critic_review", capability="critic")
    graph = TaskGraph(tasks=[first, second, third])

    decision = TaskScheduler().schedule(
        graph,
        {},
        SchedulerLimits(max_concurrent_tasks=2, remaining_budget=10),
    )

    assert [task.id for task in decision.to_dispatch] == [first.id, second.id]
    assert decision.ready_task_ids == [first.id, second.id, third.id]


def test_dependent_task_waits_until_dependency_succeeds() -> None:
    first = _task("literature_search")
    second = _task("gap_analysis", dependencies=[first.id])
    graph = TaskGraph(tasks=[first, second])

    decision = TaskScheduler().schedule(
        graph,
        {first.id: TaskExecutionState(status=TaskStatus.RUNNING)},
        SchedulerLimits(max_concurrent_tasks=2, remaining_budget=10),
    )

    assert decision.to_dispatch == []
    assert decision.waiting_task_ids == [second.id]


def test_dependent_task_becomes_ready_after_dependency_succeeds() -> None:
    first = _task("literature_search")
    second = _task("gap_analysis", dependencies=[first.id])
    graph = TaskGraph(tasks=[first, second])

    decision = TaskScheduler().schedule(
        graph,
        {first.id: TaskExecutionState(status=TaskStatus.SUCCEEDED)},
        SchedulerLimits(max_concurrent_tasks=2, remaining_budget=10),
    )

    assert [task.id for task in decision.to_dispatch] == [second.id]


def test_budget_limit_blocks_tasks_that_would_exceed_remaining_budget() -> None:
    cheap = _task("cheap", estimated_cost=1.0)
    expensive = _task("expensive", estimated_cost=5.0)
    graph = TaskGraph(tasks=[cheap, expensive])

    decision = TaskScheduler().schedule(
        graph,
        {},
        SchedulerLimits(max_concurrent_tasks=2, remaining_budget=1.0),
    )

    assert [task.id for task in decision.to_dispatch] == [cheap.id]
    assert decision.budget_blocked_task_ids == [expensive.id]


def test_per_capability_limit_is_enforced() -> None:
    first = _task("lit_1", capability="literature")
    second = _task("lit_2", capability="literature")
    dataset = _task("dataset", capability="dataset")
    graph = TaskGraph(tasks=[first, second, dataset])

    decision = TaskScheduler().schedule(
        graph,
        {},
        SchedulerLimits(
            max_concurrent_tasks=3,
            remaining_budget=10,
            per_capability_limits={"literature": 1, "dataset": 1},
        ),
    )

    assert [task.id for task in decision.to_dispatch] == [first.id, dataset.id]


def test_failed_task_retries_until_max_retries() -> None:
    task = _task("retryable", max_retries=2)
    graph = TaskGraph(tasks=[task])

    decision = TaskScheduler().schedule(
        graph,
        {task.id: TaskExecutionState(status=TaskStatus.FAILED, retry_count=1)},
        SchedulerLimits(max_concurrent_tasks=1, remaining_budget=10),
    )

    assert [retry.id for retry in decision.to_dispatch] == [task.id]


def test_exhausted_failure_skips_dependents() -> None:
    first = _task("failed", max_retries=1)
    second = _task("dependent", dependencies=[first.id])
    graph = TaskGraph(tasks=[first, second])

    decision = TaskScheduler().schedule(
        graph,
        {first.id: TaskExecutionState(status=TaskStatus.FAILED, retry_count=1)},
        SchedulerLimits(max_concurrent_tasks=2, remaining_budget=10),
    )

    assert decision.permanent_failure_task_ids == [first.id]
    assert decision.skipped_task_ids == [second.id]


def test_cancelled_tasks_are_not_dispatched_and_dependents_skip() -> None:
    first = _task("cancelled")
    second = _task("dependent", dependencies=[first.id])
    graph = TaskGraph(tasks=[first, second])

    decision = TaskScheduler().schedule(
        graph,
        {first.id: TaskExecutionState(status=TaskStatus.CANCELLED)},
        SchedulerLimits(max_concurrent_tasks=2, remaining_budget=10),
    )

    assert decision.cancelled_task_ids == [first.id]
    assert decision.skipped_task_ids == [second.id]
    assert decision.to_dispatch == []


def test_unknown_state_task_is_rejected() -> None:
    graph = TaskGraph(tasks=[_task("known")])

    with pytest.raises(TaskSchedulerError):
        TaskScheduler().schedule(
            graph,
            {uuid4(): TaskExecutionState(status=TaskStatus.RUNNING)},
            SchedulerLimits(max_concurrent_tasks=1, remaining_budget=10),
        )
