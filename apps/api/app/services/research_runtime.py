from datetime import UTC, datetime
from uuid import UUID, uuid4

from apps.api.app.domain.research.models import (
    ResearchCheckpoint,
    ResearchRun,
    ResearchRunStatus,
    ResearchState,
    RuntimeNode,
)
from apps.api.app.repositories.research_runtime import ResearchRuntimeRepository

RUNTIME_SEQUENCE = [
    RuntimeNode.START,
    RuntimeNode.INTENT,
    RuntimeNode.CONTEXT_COMPILER,
    RuntimeNode.PLANNER,
    RuntimeNode.TASK_SCHEDULER,
    RuntimeNode.ANSWER_COMPOSER,
    RuntimeNode.MEMORY_UPDATE,
    RuntimeNode.END,
]


class ResearchRunNotFoundError(Exception):
    """Raised when a research run is missing or inaccessible."""


class ResearchRuntime:
    def __init__(
        self,
        repository: ResearchRuntimeRepository,
        failing_nodes: dict[RuntimeNode, str] | None = None,
    ) -> None:
        self._repository = repository
        self._failing_nodes = failing_nodes or {}

    def create_initial_state(
        self,
        research_run_id: UUID,
        user_id: UUID,
        project_id: UUID,
        goal: str,
    ) -> ResearchState:
        return ResearchState(
            research_run_id=research_run_id,
            user_id=user_id,
            project_id=project_id,
            goal=goal,
        )

    async def start_run(
        self,
        organization_id: UUID,
        user_id: UUID,
        project_id: UUID,
        goal: str,
    ) -> ResearchRun:
        research_run_id = uuid4()
        state = self.create_initial_state(
            research_run_id=research_run_id,
            user_id=user_id,
            project_id=project_id,
            goal=goal,
        )
        now = datetime.now(UTC)
        run = ResearchRun(
            id=research_run_id,
            organization_id=organization_id,
            user_id=user_id,
            project_id=project_id,
            thread_id=f"research-run-{research_run_id}",
            status=ResearchRunStatus.PENDING,
            state=state,
            checkpoint=ResearchCheckpoint(node=RuntimeNode.START, sequence=0),
            created_at=now,
            updated_at=now,
            completed_at=None,
        )
        return await self._repository.create_run(run)

    async def run_until_interrupt(
        self,
        organization_id: UUID,
        research_run_id: UUID,
        max_nodes: int,
    ) -> ResearchRun:
        return await self._advance(
            organization_id=organization_id,
            research_run_id=research_run_id,
            max_nodes=max_nodes,
            interrupt_when_limit_reached=True,
        )

    async def resume(self, organization_id: UUID, research_run_id: UUID) -> ResearchRun:
        return await self._advance(
            organization_id=organization_id,
            research_run_id=research_run_id,
            max_nodes=None,
            interrupt_when_limit_reached=False,
        )

    async def _advance(
        self,
        organization_id: UUID,
        research_run_id: UUID,
        max_nodes: int | None,
        interrupt_when_limit_reached: bool,
    ) -> ResearchRun:
        run = await self._repository.get_run(organization_id, research_run_id)
        if run is None:
            raise ResearchRunNotFoundError("Research run not found")
        current_sequence = run.checkpoint.sequence
        if run.status == ResearchRunStatus.FAILED and run.checkpoint.error is not None:
            current_sequence = max(0, current_sequence - 1)
        executed = 0
        while current_sequence < len(RUNTIME_SEQUENCE) - 1:
            if max_nodes is not None and executed >= max_nodes:
                if interrupt_when_limit_reached:
                    return await self._save_status(run, ResearchRunStatus.INTERRUPTED)
                return run
            next_sequence = current_sequence + 1
            next_node = RUNTIME_SEQUENCE[next_sequence]
            if next_node in self._failing_nodes:
                failed = run.model_copy(
                    update={
                        "status": ResearchRunStatus.FAILED,
                        "checkpoint": ResearchCheckpoint(
                            node=next_node,
                            sequence=next_sequence,
                            error=self._failing_nodes[next_node],
                        ),
                        "completed_at": datetime.now(UTC),
                    }
                )
                return await self._repository.save_run(failed)
            run = await self._execute_node(run, next_node, next_sequence)
            current_sequence = next_sequence
            executed += 1
        return await self._save_status(run, ResearchRunStatus.SUCCEEDED, completed=True)

    async def _execute_node(
        self,
        run: ResearchRun,
        node: RuntimeNode,
        sequence: int,
    ) -> ResearchRun:
        state = run.state
        if node == RuntimeNode.INTENT:
            state = state.model_copy(update={"open_question_ids": [uuid4()]})
        elif node == RuntimeNode.PLANNER:
            state = state.model_copy(update={"task_ids": [uuid4()]})
        elif node == RuntimeNode.MEMORY_UPDATE:
            state = state.model_copy(update={"decision_ids": [uuid4()]})
        updated = run.model_copy(
            update={
                "status": ResearchRunStatus.RUNNING,
                "state": state,
                "checkpoint": ResearchCheckpoint(node=node, sequence=sequence),
            }
        )
        return await self._repository.save_run(updated)

    async def _save_status(
        self,
        run: ResearchRun,
        status: ResearchRunStatus,
        completed: bool = False,
    ) -> ResearchRun:
        updated = run.model_copy(
            update={
                "status": status,
                "completed_at": datetime.now(UTC) if completed else run.completed_at,
            }
        )
        return await self._repository.save_run(updated)
