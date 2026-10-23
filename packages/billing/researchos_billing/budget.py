from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class BudgetMode(StrEnum):
    QUICK = "QUICK"
    DEEP = "DEEP"
    EXHAUSTIVE = "EXHAUSTIVE"
    CUSTOM = "CUSTOM"


class TaskBudgetStatus(StrEnum):
    RESERVED = "RESERVED"
    SKIPPED = "SKIPPED"


class PlannedTask(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(min_length=1)
    estimated_credits: float = Field(ge=0.0)
    status: TaskBudgetStatus | None = None
    reason: str | None = None


class BudgetRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    mode: BudgetMode
    authorized_credits: float = Field(ge=0.0)
    tasks: list[PlannedTask] = Field(min_length=1)
    custom_limit: float | None = Field(default=None, ge=0.0)


class BudgetPlan(BaseModel):
    model_config = ConfigDict(frozen=True)

    mode: BudgetMode
    tasks: list[PlannedTask]
    estimated_credits: float
    reserved_credits: float
    released_credits: float = 0.0


class BudgetPlanner:
    async def plan(self, request: BudgetRequest) -> BudgetPlan:
        if request.mode == BudgetMode.CUSTOM and request.custom_limit is None:
            raise ValueError("custom budget mode requires custom_limit")
        limit: float = request.authorized_credits
        if request.mode == BudgetMode.CUSTOM:
            custom_limit = request.custom_limit
            if custom_limit is None:
                raise ValueError("custom budget mode requires custom_limit")
            limit = min(custom_limit, request.authorized_credits)
        estimated = round(sum(task.estimated_credits for task in request.tasks), 6)
        remaining = limit
        planned: list[PlannedTask] = []
        reserved = 0.0
        for task in request.tasks:
            if task.estimated_credits <= remaining:
                planned.append(task.model_copy(update={"status": TaskBudgetStatus.RESERVED}))
                reserved += task.estimated_credits
                remaining -= task.estimated_credits
            else:
                planned.append(
                    task.model_copy(
                        update={
                            "status": TaskBudgetStatus.SKIPPED,
                            "reason": "Budget exhausted before task reservation.",
                        }
                    )
                )
        return BudgetPlan(
            mode=request.mode,
            tasks=planned,
            estimated_credits=estimated,
            reserved_credits=round(reserved, 6),
        )

    async def release_unused(self, plan: BudgetPlan, actual_credits: float) -> BudgetPlan:
        if actual_credits < 0 or actual_credits > plan.reserved_credits:
            raise ValueError("actual usage must be within reserved credits")
        released = round(plan.reserved_credits - actual_credits, 6)
        return plan.model_copy(
            update={
                "reserved_credits": round(actual_credits, 6),
                "released_credits": round(plan.released_credits + released, 6),
            }
        )
