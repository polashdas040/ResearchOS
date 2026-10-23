from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class MemoryClass(StrEnum):
    CONVERSATION = "CONVERSATION"
    PROJECT_SEMANTIC = "PROJECT_SEMANTIC"
    EPISODIC = "EPISODIC"
    DECISION = "DECISION"


class MemoryStatus(StrEnum):
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"


class MemoryCandidate(BaseModel):
    model_config = ConfigDict(frozen=True)

    memory_class: MemoryClass
    content: str = Field(min_length=1, max_length=20_000)
    importance_score: float = Field(ge=0.0, le=1.0)
    source_message_ids: list[UUID] = Field(default_factory=list)


class Memory(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    organization_id: UUID
    project_id: UUID
    user_id: UUID
    conversation_id: UUID | None
    memory_class: MemoryClass
    content: str
    importance_score: float
    source_message_ids: list[UUID]
    status: MemoryStatus = MemoryStatus.ACTIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
