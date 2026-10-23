from uuid import uuid4

import pytest

from apps.api.app.domain.research.models import ResearchState
from apps.api.app.services.dynamic_planner import (
    DynamicPlanner,
    PlannerValidationError,
    ProposedTask,
    ResourceBudget,
    TaskGraph,
)


def test_dynamic_planner_returns_structured_task_graph() -> None:
    planner = DynamicPlanner()
    state = research_state("Find research gaps in multimodal Alzheimer's detection.")

    graph = planner.plan(
        state=state,
        available_capabilities=["literature", "dataset", "critic"],
        budget=ResourceBudget(max_tasks=8, max_estimated_cost=10.0),
    )

    assert isinstance(graph, TaskGraph)
    assert graph.tasks
    assert all(task.research_run_id == state.research_run_id for task in graph.tasks)
    assert all(task.objective for task in graph.tasks)
    assert all(task.assigned_capability for task in graph.tasks)
    assert graph.estimated_total_cost > 0


def test_dynamic_planner_validates_dependencies_exist() -> None:
    graph = TaskGraph(
        tasks=[
            ProposedTask(
                task_type="gap_analysis",
                objective="Find gaps.",
                assigned_capability="literature",
                dependencies=[uuid4()],
            )
        ]
    )

    with pytest.raises(PlannerValidationError, match="unknown dependency"):
        graph.validate_graph()


def test_dynamic_planner_rejects_cycles() -> None:
    first = ProposedTask(
        task_type="literature_search",
        objective="Search literature.",
        assigned_capability="literature",
    )
    second = ProposedTask(
        task_type="gap_analysis",
        objective="Analyze gaps.",
        assigned_capability="literature",
        dependencies=[first.id],
    )
    first = first.model_copy(update={"dependencies": [second.id]})
    graph = TaskGraph(tasks=[first, second])

    with pytest.raises(PlannerValidationError, match="cycle"):
        graph.validate_graph()


def test_dynamic_planner_enforces_maximum_task_limit() -> None:
    planner = DynamicPlanner()

    with pytest.raises(PlannerValidationError, match="maximum task limit"):
        planner.plan(
            state=research_state("Large review."),
            available_capabilities=["literature", "dataset", "critic"],
            budget=ResourceBudget(max_tasks=2, max_estimated_cost=10.0),
        )


def test_dynamic_planner_rejects_budget_overrun() -> None:
    planner = DynamicPlanner()

    with pytest.raises(PlannerValidationError, match="budget"):
        planner.plan(
            state=research_state("Large review."),
            available_capabilities=["literature", "dataset", "critic"],
            budget=ResourceBudget(max_tasks=8, max_estimated_cost=0.01),
        )


def test_dynamic_planner_requires_available_capabilities() -> None:
    planner = DynamicPlanner()

    with pytest.raises(PlannerValidationError, match="capability"):
        planner.plan(
            state=research_state("Analyze dataset and literature."),
            available_capabilities=["literature"],
            budget=ResourceBudget(max_tasks=8, max_estimated_cost=10.0),
        )


def research_state(goal: str) -> ResearchState:
    return ResearchState(
        research_run_id=uuid4(),
        user_id=uuid4(),
        project_id=uuid4(),
        goal=goal,
    )
