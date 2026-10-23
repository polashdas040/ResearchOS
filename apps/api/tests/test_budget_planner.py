from uuid import uuid4

import pytest

from packages.billing.researchos_billing.budget import (
    BudgetMode,
    BudgetPlanner,
    BudgetRequest,
    PlannedTask,
    TaskBudgetStatus,
)


def task(name: str, cost: float) -> PlannedTask:
    return PlannedTask(id=uuid4(), name=name, estimated_credits=cost)


@pytest.mark.asyncio
async def test_budget_planner_estimates_mode_and_limits_tasks() -> None:
    result = await BudgetPlanner().plan(
        BudgetRequest(
            mode=BudgetMode.QUICK,
            authorized_credits=10,
            tasks=[task("search", 3), task("profile", 4), task("experiment", 8)],
        )
    )

    assert result.mode == BudgetMode.QUICK
    assert result.estimated_credits == 15
    assert result.reserved_credits == 7
    assert result.tasks[0].status == TaskBudgetStatus.RESERVED
    assert result.tasks[1].status == TaskBudgetStatus.RESERVED
    assert result.tasks[2].status == TaskBudgetStatus.SKIPPED
    assert result.tasks[2].reason


@pytest.mark.asyncio
async def test_custom_budget_releases_unused_reservation() -> None:
    result = await BudgetPlanner().plan(
        BudgetRequest(
            mode=BudgetMode.CUSTOM,
            authorized_credits=5,
            custom_limit=4,
            tasks=[task("search", 2), task("profile", 2)],
        )
    )

    assert result.reserved_credits == 4
    released = await BudgetPlanner().release_unused(result, actual_credits=3)
    assert released.released_credits == 1
    assert released.reserved_credits == 3


@pytest.mark.asyncio
async def test_custom_budget_cannot_exceed_authorized_credits() -> None:
    result = await BudgetPlanner().plan(
        BudgetRequest(
            mode=BudgetMode.CUSTOM,
            authorized_credits=5,
            custom_limit=12,
            tasks=[task("deep-search", 8), task("profile", 2)],
        )
    )

    assert result.reserved_credits == 2
    assert result.tasks[0].status == TaskBudgetStatus.SKIPPED
    assert result.tasks[1].status == TaskBudgetStatus.RESERVED
