from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from apps.api.app.domain.jobs.models import JobStatus, JobType


class JobCreateRequest(BaseModel):
    job_type: JobType
    payload: dict[str, object] = Field(default_factory=dict)
    max_attempts: int = Field(default=3, ge=1, le=10)
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=200)


class JobResponse(BaseModel):
    id: UUID
    organization_id: UUID
    created_by_user_id: UUID
    job_type: JobType
    payload: dict[str, object]
    status: JobStatus
    result: dict[str, object] | None
    error: str | None
    attempts: int
    max_attempts: int
    idempotency_key: str | None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
