from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from apps.api.app.domain.research.models import ResearchState


class PlannerValidationError(Exception):
    """Raised when a generated task graph violates planner constraints."""


class ResourceBudget(BaseModel):
    model_config = ConfigDict(frozen=True)

    max_tasks: int = Field(gt=0)
    max_estimated_cost: float = Field(ge=0.0)


class ProposedTask(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    research_run_id: UUID | None = None
    task_type: str = Field(min_length=1, max_length=100)
    objective: str = Field(min_length=1, max_length=1000)
    inputs: dict[str, object] = Field(default_factory=dict)
    dependencies: list[UUID] = Field(default_factory=list)
    assigned_capability: str = Field(min_length=1, max_length=100)
    estimated_cost: float = Field(default=1.0, ge=0.0)
    max_retries: int = Field(default=1, ge=0)


class TaskGraph(BaseModel):
    model_config = ConfigDict(frozen=True)

    tasks: list[ProposedTask] = Field(default_factory=list)
    estimated_total_cost: float = 0.0

    def validate_graph(self) -> None:
        task_ids = {task.id for task in self.tasks}
        for task in self.tasks:
            unknown = [dependency for dependency in task.dependencies if dependency not in task_ids]
            if unknown:
                raise PlannerValidationError(f"Task {task.id} has unknown dependency {unknown[0]}")
        if _has_cycle(self.tasks):
            raise PlannerValidationError("Task graph contains a dependency cycle")


class DynamicPlanner:
    def plan(
        self,
        state: ResearchState,
        available_capabilities: list[str],
        budget: ResourceBudget,
    ) -> TaskGraph:
        normalized_capabilities = {capability.lower() for capability in available_capabilities}
        tasks = _default_tasks(state)
        missing_capabilities = {
            task.assigned_capability
            for task in tasks
            if task.assigned_capability.lower() not in normalized_capabilities
        }
        if missing_capabilities:
            missing = ", ".join(sorted(missing_capabilities))
            raise PlannerValidationError(f"Missing required capability: {missing}")
        if len(tasks) > budget.max_tasks:
            raise PlannerValidationError("Generated task graph exceeds maximum task limit")
        estimated_total_cost = sum(task.estimated_cost for task in tasks)
        if estimated_total_cost > budget.max_estimated_cost:
            raise PlannerValidationError("Generated task graph exceeds budget")
        graph = TaskGraph(tasks=tasks, estimated_total_cost=estimated_total_cost)
        graph.validate_graph()
        return graph


def _default_tasks(state: ResearchState) -> list[ProposedTask]:
    literature = ProposedTask(
        research_run_id=state.research_run_id,
        task_type="literature_search",
        objective=f"Find relevant prior work for: {state.goal}",
        inputs={"goal": state.goal},
        assigned_capability="literature",
        estimated_cost=1.5,
    )
    dataset = ProposedTask(
        research_run_id=state.research_run_id,
        task_type="dataset_profile",
        objective="Profile available datasets and benchmark constraints.",
        inputs={"project_id": str(state.project_id)},
        assigned_capability="dataset",
        estimated_cost=1.0,
    )
    gap_analysis = ProposedTask(
        research_run_id=state.research_run_id,
        task_type="gap_analysis",
        objective="Identify evidence-backed research gaps from literature and data constraints.",
        dependencies=[literature.id, dataset.id],
        assigned_capability="literature",
        estimated_cost=1.25,
    )
    critic = ProposedTask(
        research_run_id=state.research_run_id,
        task_type="critic_review",
        objective="Review generated gaps for overclaiming, weak evidence, and feasibility risks.",
        dependencies=[gap_analysis.id],
        assigned_capability="critic",
        estimated_cost=1.0,
    )
    return [literature, dataset, gap_analysis, critic]


def _has_cycle(tasks: list[ProposedTask]) -> bool:
    by_id = {task.id: task for task in tasks}
    visiting: set[UUID] = set()
    visited: set[UUID] = set()

    def visit(task_id: UUID) -> bool:
        if task_id in visiting:
            return True
        if task_id in visited:
            return False
        visiting.add(task_id)
        task = by_id[task_id]
        for dependency in task.dependencies:
            if dependency in by_id and visit(dependency):
                return True
        visiting.remove(task_id)
        visited.add(task_id)
        return False

    return any(visit(task.id) for task in tasks)
