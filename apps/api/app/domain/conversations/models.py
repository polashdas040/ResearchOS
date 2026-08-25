from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MessageType(StrEnum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM_EVENT = "SYSTEM_EVENT"
    TOOL_EVENT = "TOOL_EVENT"


class Conversation(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    project_id: UUID
    organization_id: UUID
    created_by_user_id: UUID
    title: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class Message(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    conversation_id: UUID
    project_id: UUID
    organization_id: UUID
    created_by_user_id: UUID
    message_type: MessageType
    content: str
    created_at: datetime
