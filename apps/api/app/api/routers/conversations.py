from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from apps.api.app.api.dependencies import get_current_user
from apps.api.app.api.routers.projects import get_project_service
from apps.api.app.domain.conversations.models import Conversation, Message
from apps.api.app.domain.users.models import User
from apps.api.app.schemas.conversations import (
    ConversationResponse,
    MessageCreateRequest,
    MessageListResponse,
    MessageResponse,
)
from apps.api.app.services.projects import ProjectService, ResourceNotFoundError

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ProjectService, Depends(get_project_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ConversationResponse:
    try:
        conversation, messages, total = await service.get_conversation_with_messages(
            user=current_user,
            conversation_id=conversation_id,
            limit=limit,
            offset=offset,
        )
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        ) from exc
    return _conversation_response(
        conversation,
        messages=MessageListResponse(
            items=[_message_response(message) for message in messages],
            total=total,
            limit=limit,
            offset=offset,
        ),
    )


@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=201)
async def create_message(
    conversation_id: UUID,
    request: MessageCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> MessageResponse:
    try:
        message = await service.create_message(
            user=current_user,
            conversation_id=conversation_id,
            message_type=request.message_type,
            content=request.content,
        )
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        ) from exc
    return _message_response(message)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> Response:
    try:
        await service.delete_conversation(current_user, conversation_id)
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _conversation_response(
    conversation: Conversation,
    messages: MessageListResponse | None = None,
) -> ConversationResponse:
    return ConversationResponse(
        id=conversation.id,
        project_id=conversation.project_id,
        organization_id=conversation.organization_id,
        created_by_user_id=conversation.created_by_user_id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=messages,
    )


def _message_response(message: Message) -> MessageResponse:
    return MessageResponse(
        id=message.id,
        conversation_id=message.conversation_id,
        project_id=message.project_id,
        organization_id=message.organization_id,
        created_by_user_id=message.created_by_user_id,
        message_type=message.message_type,
        content=message.content,
        created_at=message.created_at,
    )
