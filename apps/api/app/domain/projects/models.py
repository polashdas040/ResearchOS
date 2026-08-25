from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class Project(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    organization_id: UUID
    created_by_user_id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

