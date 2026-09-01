from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.db.models.jobs import JobRecord
from apps.api.app.domain.jobs.models import Job, JobStatus, JobType


class JobRepository(Protocol):
    async def create_job(
        self,
        organization_id: UUID | str,
        created_by_user_id: UUID | str,
        job_type: JobType | str,
        payload: dict[str, object],
        max_attempts: int = 3,
        idempotency_key: str | None = None,
    ) -> Job: ...

    async def get_job(self, job_id: UUID, organization_id: UUID | str) -> Job | None: ...

    async def claim_next_job(self) -> Job | None: ...

    async def mark_succeeded(self, job_id: UUID, result: dict[str, object]) -> Job | None: ...

    async def mark_failed(self, job_id: UUID, error: str) -> Job | None: ...

    async def cancel_job(self, job_id: UUID, organization_id: UUID | str) -> Job | None: ...


def _job_from_record(record: JobRecord) -> Job:
    return Job(
        id=record.id,
        organization_id=record.organization_id,
        created_by_user_id=record.created_by_user_id,
        job_type=JobType(record.job_type),
        payload=record.payload,
        status=JobStatus(record.status),
        result=record.result,
        error=record.error,
        attempts=record.attempts,
        max_attempts=record.max_attempts,
        idempotency_key=record.idempotency_key,
        created_at=record.created_at,
        updated_at=record.updated_at,
        started_at=record.started_at,
        completed_at=record.completed_at,
    )


class SqlAlchemyJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_job(
        self,
        organization_id: UUID | str,
        created_by_user_id: UUID | str,
        job_type: JobType | str,
        payload: dict[str, object],
        max_attempts: int = 3,
        idempotency_key: str | None = None,
    ) -> Job:
        if idempotency_key is not None:
            existing = await self._find_idempotent(str(organization_id), idempotency_key)
            if existing is not None:
                return existing
        now = datetime.now(UTC)
        record = JobRecord(
            id=uuid4(),
            organization_id=UUID(str(organization_id)),
            created_by_user_id=UUID(str(created_by_user_id)),
            job_type=str(job_type),
            payload=payload,
            status=JobStatus.QUEUED.value,
            result=None,
            error=None,
            attempts=0,
            max_attempts=max_attempts,
            idempotency_key=idempotency_key,
            created_at=now,
            updated_at=now,
            started_at=None,
            completed_at=None,
        )
        self._session.add(record)
        await self._session.flush()
        return _job_from_record(record)

    async def get_job(self, job_id: UUID, organization_id: UUID | str) -> Job | None:
        result = await self._session.execute(
            select(JobRecord).where(
                JobRecord.id == job_id,
                JobRecord.organization_id == UUID(str(organization_id)),
            )
        )
        record = result.scalar_one_or_none()
        return None if record is None else _job_from_record(record)

    async def claim_next_job(self) -> Job | None:
        result = await self._session.execute(
            select(JobRecord)
            .where(JobRecord.status.in_([JobStatus.QUEUED.value, JobStatus.RETRYING.value]))
            .order_by(JobRecord.created_at, JobRecord.id)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        record = result.scalar_one_or_none()
        if record is None:
            return None
        record.status = JobStatus.RUNNING.value
        record.attempts += 1
        record.error = None
        record.started_at = datetime.now(UTC)
        record.updated_at = record.started_at
        await self._session.flush()
        return _job_from_record(record)

    async def mark_succeeded(self, job_id: UUID, result: dict[str, object]) -> Job | None:
        return await self._complete(job_id, JobStatus.SUCCEEDED, result=result, error=None)

    async def mark_failed(self, job_id: UUID, error: str) -> Job | None:
        record = await self._record(job_id)
        if record is None:
            return None
        record.status = (
            JobStatus.RETRYING.value
            if record.attempts < record.max_attempts
            else JobStatus.FAILED.value
        )
        record.error = error
        record.updated_at = datetime.now(UTC)
        if record.status == JobStatus.FAILED.value:
            record.completed_at = record.updated_at
        await self._session.flush()
        return _job_from_record(record)

    async def cancel_job(self, job_id: UUID, organization_id: UUID | str) -> Job | None:
        record = await self._record(job_id, UUID(str(organization_id)))
        if record is None:
            return None
        record.status = JobStatus.CANCELLED.value
        record.updated_at = datetime.now(UTC)
        record.completed_at = record.updated_at
        await self._session.flush()
        return _job_from_record(record)

    async def _complete(
        self,
        job_id: UUID,
        status: JobStatus,
        result: dict[str, object] | None,
        error: str | None,
    ) -> Job | None:
        record = await self._record(job_id)
        if record is None:
            return None
        record.status = status.value
        record.result = result
        record.error = error
        record.updated_at = datetime.now(UTC)
        record.completed_at = record.updated_at
        await self._session.flush()
        return _job_from_record(record)

    async def _record(
        self,
        job_id: UUID,
        organization_id: UUID | None = None,
    ) -> JobRecord | None:
        criteria = [JobRecord.id == job_id]
        if organization_id is not None:
            criteria.append(JobRecord.organization_id == organization_id)
        result = await self._session.execute(select(JobRecord).where(*criteria))
        return result.scalar_one_or_none()

    async def _find_idempotent(self, organization_id: str, key: str) -> Job | None:
        result = await self._session.execute(
            select(JobRecord).where(
                JobRecord.organization_id == UUID(organization_id),
                JobRecord.idempotency_key == key,
            )
        )
        record = result.scalar_one_or_none()
        return None if record is None else _job_from_record(record)


class InMemoryJobRepository:
    def __init__(self) -> None:
        self._jobs: dict[UUID, Job] = {}

    async def create_job(
        self,
        organization_id: UUID | str,
        created_by_user_id: UUID | str,
        job_type: JobType | str,
        payload: dict[str, object],
        max_attempts: int = 3,
        idempotency_key: str | None = None,
    ) -> Job:
        if idempotency_key is not None:
            for job in self._jobs.values():
                if (
                    job.organization_id == UUID(str(organization_id))
                    and job.idempotency_key == idempotency_key
                ):
                    return job
        now = datetime.now(UTC)
        job = Job(
            id=uuid4(),
            organization_id=UUID(str(organization_id)),
            created_by_user_id=UUID(str(created_by_user_id)),
            job_type=JobType(str(job_type)),
            payload=payload,
            status=JobStatus.QUEUED,
            result=None,
            error=None,
            attempts=0,
            max_attempts=max_attempts,
            idempotency_key=idempotency_key,
            created_at=now,
            updated_at=now,
            started_at=None,
            completed_at=None,
        )
        self._jobs[job.id] = job
        return job

    async def get_job(self, job_id: UUID, organization_id: UUID | str) -> Job | None:
        job = self._jobs.get(job_id)
        if job is None or job.organization_id != UUID(str(organization_id)):
            return None
        return job

    async def claim_next_job(self) -> Job | None:
        runnable = [
            job
            for job in self._jobs.values()
            if job.status in {JobStatus.QUEUED, JobStatus.RETRYING}
        ]
        if not runnable:
            return None
        job = sorted(runnable, key=lambda item: (item.created_at, item.id))[0]
        claimed = job.model_copy(
            update={
                "status": JobStatus.RUNNING,
                "attempts": job.attempts + 1,
                "error": None,
                "started_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            }
        )
        self._jobs[job.id] = claimed
        return claimed

    async def mark_succeeded(self, job_id: UUID, result: dict[str, object]) -> Job | None:
        job = self._jobs.get(job_id)
        if job is None:
            return None
        completed = job.model_copy(
            update={
                "status": JobStatus.SUCCEEDED,
                "result": result,
                "error": None,
                "updated_at": datetime.now(UTC),
                "completed_at": datetime.now(UTC),
            }
        )
        self._jobs[job_id] = completed
        return completed

    async def mark_failed(self, job_id: UUID, error: str) -> Job | None:
        job = self._jobs.get(job_id)
        if job is None:
            return None
        status = JobStatus.RETRYING if job.attempts < job.max_attempts else JobStatus.FAILED
        failed = job.model_copy(
            update={
                "status": status,
                "error": error,
                "updated_at": datetime.now(UTC),
                "completed_at": datetime.now(UTC) if status == JobStatus.FAILED else None,
            }
        )
        self._jobs[job_id] = failed
        return failed

    async def cancel_job(self, job_id: UUID, organization_id: UUID | str) -> Job | None:
        job = await self.get_job(job_id, organization_id)
        if job is None:
            return None
        cancelled = job.model_copy(
            update={
                "status": JobStatus.CANCELLED,
                "updated_at": datetime.now(UTC),
                "completed_at": datetime.now(UTC),
            }
        )
        self._jobs[job_id] = cancelled
        return cancelled
