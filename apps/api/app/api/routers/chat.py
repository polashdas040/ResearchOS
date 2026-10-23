import json
from collections.abc import AsyncIterator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.api.dependencies import get_current_user, get_db_session
from apps.api.app.api.routers.files import get_file_service
from apps.api.app.api.routers.projects import get_project_service
from apps.api.app.config import Settings, get_settings
from apps.api.app.domain.users.models import User
from apps.api.app.repositories.usage import SqlAlchemyUsageRepository, UsageRepository
from apps.api.app.schemas.chat import ChatStreamRequest
from apps.api.app.services.chat_streaming import ChatStreamEvent, ChatStreamingService
from apps.api.app.services.document_context import DocumentContextService
from apps.api.app.services.files import FileService
from apps.api.app.services.model_gateway import (
    DeterministicModelGateway,
    GeminiModelGateway,
    ModelGateway,
    OllamaModelGateway,
    OpenAICompatibleModelGateway,
    OpenAIModelGateway,
)
from apps.api.app.services.projects import ProjectService, ResourceNotFoundError

router = APIRouter(prefix="/conversations", tags=["chat"])


def get_model_gateway(settings: Annotated[Settings, Depends(get_settings)]) -> ModelGateway:
    if settings.gemini_api_key:
        return GeminiModelGateway(
            api_key=settings.gemini_api_key,
            model_name=settings.gemini_chat_model,
        )
    if settings.openai_compatible_api_key and settings.openai_compatible_base_url:
        compatible_base_url = str(settings.openai_compatible_base_url)
        if _is_ollama_base_url(compatible_base_url):
            return OllamaModelGateway(
                base_url=_ollama_native_base_url(compatible_base_url),
                model_name=settings.openai_compatible_chat_model,
            )
        return OpenAICompatibleModelGateway(
            api_key=settings.openai_compatible_api_key,
            base_url=compatible_base_url,
            model_name=settings.openai_compatible_chat_model,
            timeout_seconds=settings.model_provider_timeout_seconds,
        )
    if settings.openai_api_key:
        return OpenAIModelGateway(
            api_key=settings.openai_api_key,
            model_name=settings.openai_chat_model,
            timeout_seconds=settings.model_provider_timeout_seconds,
        )
    return DeterministicModelGateway()


def get_usage_repository(
    session: Annotated[AsyncSession, Depends(get_db_session, scope="function")],
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


def get_document_context_service(
    file_service: Annotated[FileService, Depends(get_file_service)],
) -> DocumentContextService:
    return DocumentContextService(file_service)


@router.post("/{conversation_id}/messages/stream")
async def stream_message(
    conversation_id: UUID,
    request: ChatStreamRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ChatStreamingService, Depends(get_chat_streaming_service)],
    document_context_service: Annotated[
        DocumentContextService, Depends(get_document_context_service)
    ],
) -> StreamingResponse:
    try:
        await service.authorize_conversation(current_user, conversation_id)
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        ) from exc

    try:
        model_context = await document_context_service.build_context(
            current_user,
            request.file_ids,
            request.content,
        )
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found") from exc

    async def event_stream() -> AsyncIterator[str]:
        async for event in service.stream_message(
            user=current_user,
            conversation_id=conversation_id,
            content=request.content,
            model_context=model_context,
            history=[item.model_dump() for item in request.history],
            citation_style=request.citation_style,
            reference_context=request.reference_context,
            require_references=request.require_references,
        ):
            yield _format_sse(event)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _format_sse(event: ChatStreamEvent) -> str:
    return f"event: {event.event}\ndata: {json.dumps(event.data)}\n\n"


def _is_ollama_base_url(base_url: str) -> bool:
    return "localhost:11434" in base_url or "host.docker.internal:11434" in base_url


def _ollama_native_base_url(base_url: str) -> str:
    return base_url.removesuffix("/v1").rstrip("/")
