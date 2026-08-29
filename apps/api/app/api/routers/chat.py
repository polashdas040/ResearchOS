import json
from collections.abc import AsyncIterator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.api.dependencies import get_current_user, get_db_session
from apps.api.app.api.routers.projects import get_project_service
from apps.api.app.domain.users.models import User
from apps.api.app.repositories.usage import SqlAlchemyUsageRepository, UsageRepository
from apps.api.app.schemas.chat import ChatStreamRequest
from apps.api.app.services.chat_streaming import ChatStreamEvent, ChatStreamingService
from apps.api.app.services.model_gateway import DeterministicModelGateway, ModelGateway
from apps.api.app.services.projects import ProjectService, ResourceNotFoundError

router = APIRouter(prefix="/conversations", tags=["chat"])


def get_model_gateway() -> ModelGateway:
    return DeterministicModelGateway()


def get_usage_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UsageRepository:
    return SqlAlchemyUsageRepository(session)


def get_chat_streaming_service(
    project_service: Annotated[ProjectService, Depends(get_project_service)],
    model_gateway: Annotated[ModelGateway, Depends(get_model_gateway)],
    usage_repository: Annotated[UsageRepository, Depends(get_usage_repository)],
) -> ChatStreamingService:
    return ChatStreamingService(
        project_service=project_service,
        model_gateway=model_gateway,
        usage_repository=usage_repository,
    )


@router.post("/{conversation_id}/messages/stream")
async def stream_message(
    conversation_id: UUID,
    request: ChatStreamRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ChatStreamingService, Depends(get_chat_streaming_service)],
) -> StreamingResponse:
    try:
        await service.authorize_conversation(current_user, conversation_id)
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        ) from exc

    async def event_stream() -> AsyncIterator[str]:
        async for event in service.stream_message(
            user=current_user,
            conversation_id=conversation_id,
            content=request.content,
        ):
            yield _format_sse(event)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _format_sse(event: ChatStreamEvent) -> str:
    return f"event: {event.event}\ndata: {json.dumps(event.data)}\n\n"
