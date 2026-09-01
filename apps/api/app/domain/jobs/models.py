from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class JobStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    CANCELLED = "CANCELLED"


class JobType(StrEnum):
    DOCUMENT_PARSE = "DOCUMENT_PARSE"
    EMBED_DOCUMENT = "EMBED_DOCUMENT"
    RESEARCH_RUN = "RESEARCH_RUN"
    DATASET_PROFILE = "DATASET_PROFILE"
    EXPERIMENT = "EXPERIMENT"


class Job(BaseModel):
    model_config = ConfigDict(frozen=True)

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
