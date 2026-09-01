import pytest

from apps.api.app.repositories.jobs import InMemoryJobRepository
from apps.worker.app.jobs import JobRunner


@pytest.mark.asyncio
async def test_worker_executes_queued_job_successfully() -> None:
    repository = InMemoryJobRepository()
    job = await repository.create_job(
        organization_id="00000000-0000-0000-0000-000000000001",
        created_by_user_id="00000000-0000-0000-0000-000000000002",
        job_type="DOCUMENT_PARSE",
        payload={"file_id": "file-1"},
    )
    runner = JobRunner(repository, handlers={"DOCUMENT_PARSE": successful_handler})

    executed = await runner.run_once()
    loaded = await repository.get_job(job.id, job.organization_id)

    assert executed is True
    assert loaded is not None
    assert loaded.status == "SUCCEEDED"
    assert loaded.result == {"ok": True}


@pytest.mark.asyncio
async def test_worker_persists_failure_and_retries_until_limit() -> None:
    repository = InMemoryJobRepository()
    job = await repository.create_job(
        organization_id="00000000-0000-0000-0000-000000000001",
        created_by_user_id="00000000-0000-0000-0000-000000000002",
        job_type="DOCUMENT_PARSE",
        payload={"file_id": "file-1"},
        max_attempts=2,
    )
    runner = JobRunner(repository, handlers={"DOCUMENT_PARSE": failing_handler})

    first = await runner.run_once()
    retrying = await repository.get_job(job.id, job.organization_id)
    second = await runner.run_once()
    failed = await repository.get_job(job.id, job.organization_id)

    assert first is True
    assert second is True
    assert retrying is not None
    assert retrying.status == "RETRYING"
    assert failed is not None
    assert failed.status == "FAILED"
    assert failed.error == "handler failed"


async def successful_handler(payload: dict[str, object]) -> dict[str, object]:
    return {"ok": bool(payload)}


async def failing_handler(payload: dict[str, object]) -> dict[str, object]:
    raise RuntimeError("handler failed")
