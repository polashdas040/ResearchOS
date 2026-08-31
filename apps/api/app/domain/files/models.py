from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FileStatus(StrEnum):
    UPLOADED = "UPLOADED"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"
    DELETED = "DELETED"


class ProjectFile(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    project_id: UUID
    organization_id: UUID
    uploaded_by_user_id: UUID
    filename: str
    content_type: str
    size_bytes: int
    sha256: str
    storage_key: str
    status: FileStatus
    duplicate_of_file_id: UUID | None
    created_at: datetime
    updated_at: datetime
