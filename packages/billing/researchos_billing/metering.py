from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class ResourceUsage(BaseModel):
    model_config = ConfigDict(frozen=True)

    research_run_id: UUID
    task_id: UUID
    resources: dict[str, float] = Field(min_length=1)


class UsageRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    research_run_id: UUID
    task_id: UUID
    resources: dict[str, float]
    credits: float = Field(ge=0.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ResourceMeter:
    def __init__(self, rates: dict[str, float]) -> None:
        if any(rate < 0 for rate in rates.values()):
            raise ValueError("resource rates cannot be negative")
        self._rates = dict(rates)
        self._records: list[UsageRecord] = []

    def configure_rate(self, resource: str, rate: float) -> None:
        if not resource:
            raise ValueError("resource name is required")
        if rate < 0:
            raise ValueError("resource rates cannot be negative")
        self._rates[resource] = rate

    async def record(self, usage: ResourceUsage) -> UsageRecord:
        if any(amount < 0 for amount in usage.resources.values()):
            raise ValueError("resource usage cannot be negative")
        credits = sum(
            amount * self._rates.get(resource, 0.0)
            for resource, amount in usage.resources.items()
        )
        record = UsageRecord(
            research_run_id=usage.research_run_id,
            task_id=usage.task_id,
            resources=dict(usage.resources),
            credits=round(credits, 6),
        )
        self._records.append(record)
        return record

    async def records_for_task(self, task_id: UUID) -> list[UsageRecord]:
        return [record for record in self._records if record.task_id == task_id]

    async def task_total(self, task_id: UUID) -> float:
        return round(sum(record.credits for record in await self.records_for_task(task_id)), 6)

    async def run_total(self, research_run_id: UUID) -> float:
        return round(
            sum(
                record.credits
                for record in self._records
                if record.research_run_id == research_run_id
            ),
            6,
        )
