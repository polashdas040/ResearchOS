from collections.abc import AsyncIterator
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from apps.api.app.domain.conversations.models import MessageType
from apps.api.app.domain.users.models import User
from apps.api.app.repositories.usage import UsageRepository
from apps.api.app.services.model_gateway import (
    ChatMessageInput,
    ModelGateway,
    ModelProviderError,
    ModelRequest,
    UsageSummary,
)
from apps.api.app.services.projects import ProjectService, ResourceNotFoundError


class ChatStreamEvent(BaseModel):
    event: Literal["message.started", "message.delta", "message.completed", "message.failed"]
    data: dict[str, object]


class ChatStreamingService:
    def __init__(
        self,
        project_service: ProjectService,
        model_gateway: ModelGateway,
        usage_repository: UsageRepository,
    ) -> None:
        self._project_service = project_service
        self._model_gateway = model_gateway
        self._usage_repository = usage_repository

    async def stream_message(
        self,
        user: User,
        conversation_id: UUID,
        content: str,
    ) -> AsyncIterator[ChatStreamEvent]:
        conversation = await self._project_service.get_conversation(user, conversation_id)
        user_message = await self._project_service.create_message(
            user=user,
            conversation_id=conversation.id,
            message_type=MessageType.USER,
            content=content,
        )
        yield ChatStreamEvent(
            event="message.started",
            data={
                "conversation_id": str(conversation.id),
                "user_message_id": str(user_message.id),
            },
        )

        assistant_content = ""
        usage: UsageSummary | None = None
        model = self._model_gateway.chat_model()
        try:
            async for chunk in model.stream(
                ModelRequest(messages=[ChatMessageInput(role="user", content=content)])
            ):
                if chunk.delta:
                    assistant_content += chunk.delta
                    yield ChatStreamEvent(event="message.delta", data={"delta": chunk.delta})
                if chunk.usage is not None:
                    usage = chunk.usage
        except ModelProviderError as exc:
            yield ChatStreamEvent(event="message.failed", data={"error": str(exc)})
            return

        assistant_message = await self._project_service.create_message(
            user=user,
            conversation_id=conversation.id,
            message_type=MessageType.ASSISTANT,
            content=assistant_content,
        )
        if usage is not None:
            await self._usage_repository.record_model_usage(
                organization_id=conversation.organization_id,
                project_id=conversation.project_id,
                conversation_id=conversation.id,
                message_id=assistant_message.id,
                provider_name=getattr(self._model_gateway, "provider_name", "unknown"),
                model_name=getattr(self._model_gateway, "model_name", "unknown"),
                usage=usage,
        )
        yield ChatStreamEvent(
            event="message.completed",
            data={
                "assistant_message_id": str(assistant_message.id),
                "usage": usage.model_dump() if usage is not None else None,
            },
        )

    async def authorize_conversation(self, user: User, conversation_id: UUID) -> None:
        await self._project_service.get_conversation(user, conversation_id)


__all__ = ["ChatStreamingService", "ChatStreamEvent", "ResourceNotFoundError"]
