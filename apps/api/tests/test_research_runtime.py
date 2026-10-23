from uuid import uuid4

import pytest

from apps.api.app.domain.research.models import ResearchRunStatus, RuntimeNode
from apps.api.app.repositories.research_runtime import InMemoryResearchRuntimeRepository
from apps.api.app.services.research_runtime import ResearchRuntime


@pytest.mark.asyncio
async def test_research_runtime_persists_checkpoint_after_start() -> None:
    repository = InMemoryResearchRuntimeRepository()
    runtime = ResearchRuntime(repository)
    organization_id = uuid4()
    user_id = uuid4()
    project_id = uuid4()

    run = await runtime.start_run(
        organization_id=organization_id,
        user_id=user_id,
        project_id=project_id,
        goal="Find evidence-backed ADNI research gaps.",
    )
    loaded = await repository.get_run(organization_id, run.id)

    assert loaded is not None
    assert loaded.thread_id
    assert loaded.checkpoint.node == RuntimeNode.START
    assert loaded.state.user_id == user_id
    assert loaded.state.project_id == project_id
    assert loaded.state.goal == "Find evidence-backed ADNI research gaps."
    assert loaded.state.claim_ids == []


@pytest.mark.asyncio
async def test_interrupted_research_runtime_resumes_from_checkpoint() -> None:
    repository = InMemoryResearchRuntimeRepository()
    runtime = ResearchRuntime(repository)
    run = await runtime.start_run(
        organization_id=uuid4(),
        user_id=uuid4(),
        project_id=uuid4(),
        goal="Review a paper.",
    )

    interrupted = await runtime.run_until_interrupt(run.organization_id, run.id, max_nodes=2)
    resumed = await runtime.resume(run.organization_id, run.id)

    assert interrupted.status == ResearchRunStatus.INTERRUPTED
    assert interrupted.checkpoint.node == RuntimeNode.CONTEXT_COMPILER
    assert resumed.status == ResearchRunStatus.SUCCEEDED
    assert resumed.checkpoint.node == RuntimeNode.END
    assert resumed.state.decision_ids


@pytest.mark.asyncio
async def test_node_failure_is_persisted_and_recoverable() -> None:
    repository = InMemoryResearchRuntimeRepository()
    runtime = ResearchRuntime(
        repository,
        failing_nodes={RuntimeNode.PLANNER: "Planner provider unavailable"},
    )
    run = await runtime.start_run(
        organization_id=uuid4(),
        user_id=uuid4(),
        project_id=uuid4(),
        goal="Generate hypotheses.",
    )

    failed = await runtime.resume(run.organization_id, run.id)
    repaired_runtime = ResearchRuntime(repository)
    recovered = await repaired_runtime.resume(run.organization_id, run.id)

    assert failed.status == ResearchRunStatus.FAILED
    assert failed.checkpoint.node == RuntimeNode.PLANNER
    assert failed.checkpoint.error == "Planner provider unavailable"
    assert recovered.status == ResearchRunStatus.SUCCEEDED
    assert recovered.checkpoint.node == RuntimeNode.END
    assert recovered.state.task_ids


@pytest.mark.asyncio
async def test_cross_tenant_research_run_access_is_blocked() -> None:
    repository = InMemoryResearchRuntimeRepository()
    runtime = ResearchRuntime(repository)
    run = await runtime.start_run(
        organization_id=uuid4(),
        user_id=uuid4(),
        project_id=uuid4(),
        goal="Private research goal.",
    )

    loaded = await repository.get_run(uuid4(), run.id)

    assert loaded is None


def test_research_state_uses_references_not_full_database_objects() -> None:
    runtime = ResearchRuntime(InMemoryResearchRuntimeRepository())
    state = runtime.create_initial_state(
        research_run_id=uuid4(),
        user_id=uuid4(),
        project_id=uuid4(),
        goal="Map evidence.",
    )

    assert isinstance(state.claim_ids, list)
    assert isinstance(state.evidence_ids, list)
    assert isinstance(state.artifact_ids, list)
    assert not hasattr(state, "papers")
    assert not hasattr(state, "messages")
