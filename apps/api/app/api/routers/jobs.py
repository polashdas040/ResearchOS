from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.api.dependencies import get_current_user, get_db_session
from apps.api.app.domain.jobs.models import Job
from apps.api.app.domain.users.models import User
from apps.api.app.repositories.jobs import JobRepository, SqlAlchemyJobRepository
from apps.api.app.schemas.jobs import JobCreateRequest, JobResponse
from apps.api.app.services.jobs import JobNotFoundError, JobService

router = APIRouter(prefix="/jobs", tags=["jobs"])


def get_job_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> JobRepository:
    return SqlAlchemyJobRepository(session)


def get_job_service(
    repository: Annotated[JobRepository, Depends(get_job_repository)],
) -> JobService:
    return JobService(repository)


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    request: JobCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[JobService, Depends(get_job_service)],
) -> JobResponse:
    job = await service.create_job(
        user=current_user,
        job_type=request.job_type.value,
        payload=request.payload,
        max_attempts=request.max_attempts,
        idempotency_key=request.idempotency_key,
    )
    return _job_response(job)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[JobService, Depends(get_job_service)],
) -> JobResponse:
    try:
        return _job_response(await service.get_job(current_user, job_id))
    except JobNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found") from exc


def _job_response(job: Job) -> JobResponse:
    return JobResponse(
        id=job.id,
        organization_id=job.organization_id,
        created_by_user_id=job.created_by_user_id,
        job_type=job.job_type,
        payload=job.payload,
        status=job.status,
        result=job.result,
        error=job.error,
        attempts=job.attempts,
        max_attempts=job.max_attempts,
        idempotency_key=job.idempotency_key,
        created_at=job.created_at,
        updated_at=job.updated_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )
