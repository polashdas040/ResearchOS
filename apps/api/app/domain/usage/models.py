from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ModelUsageEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    organization_id: UUID
    project_id: UUID
    conversation_id: UUID
    message_id: UUID | None
    provider_name: str
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    created_at: datetime
