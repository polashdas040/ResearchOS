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
        model_context: str | None = None,
        history: list[dict[str, str]] | None = None,
        citation_style: str = "IEEE",
        reference_context: str = "",
        require_references: bool = False,
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
        model_content = content
        if model_context:
            model_content = (
                f"{content}\n\nUploaded file context:\n{model_context}"
                if content
                else f"Uploaded file context:\n{model_context}"
            )
        system_messages: list[ChatMessageInput] = []
        if require_references:
            verified_source_context = reference_context or model_context or ""
            system_messages.append(ChatMessageInput(
                role="system",
                content=(
                    "Answer as a research assistant. Ground factual claims in the verified source "
                    f"context and use {citation_style} citation style. Include a References "
                    "section containing only the sources cited in the answer. Preserve each "
                    "source's exact citation marker and reference entry from the context; never "
                    "reuse a marker for a different source or renumber it. Never invent a "
                    "citation. If no supplied source "
                    "supports a claim, state that limitation explicitly.\n\n"
                    "VERIFIED SOURCE CONTEXT:\n"
                    f"{verified_source_context or 'No verified sources were supplied.'}"
                ),
            ))
        history_messages: list[ChatMessageInput] = []
        for item in (history or [])[-40:]:
            role = item.get("role")
            history_content = item.get("content")
            if role not in {"user", "assistant"} or not history_content:
                continue
            typed_role: Literal["user", "assistant"] = (
                "user" if role == "user" else "assistant"
            )
            history_messages.append(ChatMessageInput(role=typed_role, content=history_content))
        try:
            async for chunk in model.stream(
                ModelRequest(messages=[
                    *system_messages,
                    *history_messages,
                    ChatMessageInput(role="user", content=model_content),
                ])
            ):
                if chunk.delta:
                    assistant_content += chunk.delta
                    yield ChatStreamEvent(event="message.delta", data={"delta": chunk.delta})
                if chunk.usage is not None:
                    usage = chunk.usage
        except ModelProviderError as exc:
            yield ChatStreamEvent(event="message.failed", data={"error": str(exc)})
            return

        should_append_references = (
            require_references
            and reference_context
            and "references" not in assistant_content.lower()
        )
        if should_append_references:
            reference_lines = _cited_reference_lines(assistant_content, reference_context)
            if reference_lines:
                bibliography = "\n\nReferences\n" + "\n".join(reference_lines)
                assistant_content += bibliography
                yield ChatStreamEvent(event="message.delta", data={"delta": bibliography})

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


def _cited_reference_lines(assistant_content: str, reference_context: str) -> list[str]:
    cited_references: list[str] = []
    for block in reference_context.split("\n\n"):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        marker_line = next(
            (line for line in lines if line.upper().startswith("INLINE CITATION:")),
            "",
        )
        marker = marker_line.partition(":")[2].strip()
        if marker and marker in assistant_content:
            cited_references.append(lines[0])
    return cited_references


__all__ = ["ChatStreamingService", "ChatStreamEvent", "ResourceNotFoundError"]
