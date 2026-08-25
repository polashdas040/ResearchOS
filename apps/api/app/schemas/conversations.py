from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from apps.api.app.domain.conversations.models import MessageType


class ConversationCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class MessageCreateRequest(BaseModel):
    message_type: MessageType
    content: str = Field(min_length=1, max_length=100_000)


class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    project_id: UUID
    organization_id: UUID
    created_by_user_id: UUID
    message_type: MessageType
    content: str
    created_at: datetime


class MessageListResponse(BaseModel):
    items: list[MessageResponse]
    total: int
    limit: int
    offset: int


class ConversationResponse(BaseModel):
    id: UUID
    project_id: UUID
    organization_id: UUID
    created_by_user_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    messages: MessageListResponse | None = None


class ConversationListResponse(BaseModel):
    items: list[ConversationResponse]
    total: int
    limit: int
    offset: int
