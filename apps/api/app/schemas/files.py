from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from apps.api.app.domain.files.models import FileStatus


class FileResponse(BaseModel):
    id: UUID
    project_id: UUID
    organization_id: UUID
    uploaded_by_user_id: UUID
    filename: str
    content_type: str
    size_bytes: int
    sha256: str
    status: FileStatus
    duplicate_of_file_id: UUID | None
    created_at: datetime
    updated_at: datetime


class FileListResponse(BaseModel):
    items: list[FileResponse]
    total: int
    limit: int
    offset: int
