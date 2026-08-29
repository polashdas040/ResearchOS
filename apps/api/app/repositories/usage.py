from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.db.models.usage import ModelUsageEventRecord
from apps.api.app.domain.usage.models import ModelUsageEvent
from apps.api.app.services.model_gateway import UsageSummary


class UsageRepository(Protocol):
    async def record_model_usage(
        self,
        organization_id: UUID,
        project_id: UUID,
        conversation_id: UUID,
        message_id: UUID | None,
        provider_name: str,
        model_name: str,
        usage: UsageSummary,
    ) -> ModelUsageEvent: ...


def _usage_from_record(record: ModelUsageEventRecord) -> ModelUsageEvent:
    return ModelUsageEvent(
        id=record.id,
        organization_id=record.organization_id,
        project_id=record.project_id,
        conversation_id=record.conversation_id,
        message_id=record.message_id,
        provider_name=record.provider_name,
        model_name=record.model_name,
        prompt_tokens=record.prompt_tokens,
        completion_tokens=record.completion_tokens,
        total_tokens=record.total_tokens,
        created_at=record.created_at,
    )


class SqlAlchemyUsageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record_model_usage(
        self,
        organization_id: UUID,
        project_id: UUID,
        conversation_id: UUID,
        message_id: UUID | None,
        provider_name: str,
        model_name: str,
        usage: UsageSummary,
    ) -> ModelUsageEvent:
        record = ModelUsageEventRecord(
            id=uuid4(),
            organization_id=organization_id,
            project_id=project_id,
            conversation_id=conversation_id,
            message_id=message_id,
            provider_name=provider_name,
            model_name=model_name,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            created_at=datetime.now(UTC),
        )
        self._session.add(record)
        await self._session.flush()
        return _usage_from_record(record)


class InMemoryUsageRepository:
    def __init__(self) -> None:
        self.events: list[ModelUsageEvent] = []

    async def record_model_usage(
        self,
        organization_id: UUID,
        project_id: UUID,
        conversation_id: UUID,
        message_id: UUID | None,
        provider_name: str,
        model_name: str,
        usage: UsageSummary,
    ) -> ModelUsageEvent:
        event = ModelUsageEvent(
            id=uuid4(),
            organization_id=organization_id,
            project_id=project_id,
            conversation_id=conversation_id,
            message_id=message_id,
            provider_name=provider_name,
            model_name=model_name,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            created_at=datetime.now(UTC),
        )
        self.events.append(event)
        return event
