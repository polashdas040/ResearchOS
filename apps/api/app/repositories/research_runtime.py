from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.db.models.research import ResearchRunRecord
from apps.api.app.domain.research.models import (
    ResearchCheckpoint,
    ResearchRun,
    ResearchRunStatus,
    ResearchState,
)


class ResearchRuntimeRepository(Protocol):
    async def create_run(self, run: ResearchRun) -> ResearchRun: ...

    async def get_run(self, organization_id: UUID, research_run_id: UUID) -> ResearchRun | None: ...

    async def save_run(self, run: ResearchRun) -> ResearchRun: ...


class SqlAlchemyResearchRuntimeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_run(self, run: ResearchRun) -> ResearchRun:
        self._session.add(_record_from_run(run))
        await self._session.flush()
        return run

    async def get_run(self, organization_id: UUID, research_run_id: UUID) -> ResearchRun | None:
        result = await self._session.execute(
            select(ResearchRunRecord).where(
                ResearchRunRecord.id == research_run_id,
                ResearchRunRecord.organization_id == organization_id,
            )
        )
        record = result.scalar_one_or_none()
        return None if record is None else _run_from_record(record)

    async def save_run(self, run: ResearchRun) -> ResearchRun:
        result = await self._session.execute(
            select(ResearchRunRecord).where(
                ResearchRunRecord.id == run.id,
                ResearchRunRecord.organization_id == run.organization_id,
            )
        )
        record = result.scalar_one_or_none()
        if record is None:
            return await self.create_run(run)
        record.status = run.status.value
        record.state = run.state.model_dump(mode="json")
        record.checkpoint = run.checkpoint.model_dump(mode="json")
        record.updated_at = datetime.now(UTC)
        record.completed_at = run.completed_at
        await self._session.flush()
        return run.model_copy(update={"updated_at": record.updated_at})


class InMemoryResearchRuntimeRepository:
    def __init__(self) -> None:
        self._runs: dict[UUID, ResearchRun] = {}

    async def create_run(self, run: ResearchRun) -> ResearchRun:
        self._runs[run.id] = run
        return run

    async def get_run(self, organization_id: UUID, research_run_id: UUID) -> ResearchRun | None:
        run = self._runs.get(research_run_id)
        if run is None or run.organization_id != organization_id:
            return None
        return run

    async def save_run(self, run: ResearchRun) -> ResearchRun:
        stored = run.model_copy(update={"updated_at": datetime.now(UTC)})
        self._runs[run.id] = stored
        return stored


def _record_from_run(run: ResearchRun) -> ResearchRunRecord:
    return ResearchRunRecord(
        id=run.id,
        organization_id=run.organization_id,
        user_id=run.user_id,
        project_id=run.project_id,
        thread_id=run.thread_id,
        status=run.status.value,
        state=run.state.model_dump(mode="json"),
        checkpoint=run.checkpoint.model_dump(mode="json"),
        created_at=run.created_at,
        updated_at=run.updated_at,
        completed_at=run.completed_at,
    )


def _run_from_record(record: ResearchRunRecord) -> ResearchRun:
    return ResearchRun(
        id=record.id,
        organization_id=record.organization_id,
        user_id=record.user_id,
        project_id=record.project_id,
        thread_id=record.thread_id,
        status=ResearchRunStatus(record.status),
        state=ResearchState.model_validate(record.state),
        checkpoint=ResearchCheckpoint.model_validate(record.checkpoint),
        created_at=record.created_at,
        updated_at=record.updated_at,
        completed_at=record.completed_at,
    )
