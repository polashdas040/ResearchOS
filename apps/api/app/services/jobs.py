from uuid import UUID

from apps.api.app.domain.jobs.models import Job
from apps.api.app.domain.users.models import User
from apps.api.app.repositories.jobs import JobRepository


class JobNotFoundError(Exception):
    """Raised when a tenant-scoped job is missing or inaccessible."""


class JobService:
    def __init__(self, repository: JobRepository) -> None:
        self._repository = repository

    async def create_job(
        self,
        user: User,
        job_type: str,
        payload: dict[str, object],
        max_attempts: int,
        idempotency_key: str | None,
    ) -> Job:
        return await self._repository.create_job(
            organization_id=user.primary_organization_id,
            created_by_user_id=user.id,
            job_type=job_type,
            payload=payload,
            max_attempts=max_attempts,
            idempotency_key=idempotency_key,
        )

    async def get_job(self, user: User, job_id: UUID) -> Job:
        job = await self._repository.get_job(job_id, user.primary_organization_id)
        if job is None:
            raise JobNotFoundError("Job not found")
        return job
