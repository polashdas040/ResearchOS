import hashlib
import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from packages.execution.researchos_execution.experiment_runner import ExperimentRun


class ReproducibilityRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    run_id: UUID
    parent_run_id: UUID | None = None
    dataset_fingerprint: str
    code_commit: str
    configuration_hash: str
    environment: dict[str, Any]
    hardware: dict[str, Any]
    seed: int
    input_artifacts: list[str]
    output_artifacts: list[str]
    metrics: dict[str, float]
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ReproducibilityLedger:
    def __init__(self) -> None:
        self._records: dict[UUID, ReproducibilityRecord] = {}

    async def record(
        self,
        run: ExperimentRun,
        input_artifacts: list[str],
        parent_run_id: UUID | None = None,
    ) -> ReproducibilityRecord:
        if run.id in self._records:
            raise ValueError(f"Reproducibility record already exists: {run.id}")
        if parent_run_id is not None and parent_run_id not in self._records:
            raise KeyError(f"Parent reproducibility record not found: {parent_run_id}")
        record = ReproducibilityRecord(
            run_id=run.id,
            parent_run_id=parent_run_id,
            dataset_fingerprint=run.dataset_fingerprint,
            code_commit=run.code_commit,
            configuration_hash=_configuration_hash(run.configuration),
            environment=dict(run.environment),
            hardware=dict(run.hardware),
            seed=run.seed,
            input_artifacts=list(input_artifacts),
            output_artifacts=list(run.output_artifacts),
            metrics=dict(run.metrics),
        )
        self._records[run.id] = record
        return record

    async def get(self, run_id: UUID) -> ReproducibilityRecord | None:
        return self._records.get(run_id)

    async def lineage(self, run_id: UUID) -> list[ReproducibilityRecord]:
        result: list[ReproducibilityRecord] = []
        visited: set[UUID] = set()
        current_id: UUID | None = run_id
        while current_id is not None:
            if current_id in visited:
                raise ValueError("Reproducibility lineage contains a cycle")
            visited.add(current_id)
            record = self._records.get(current_id)
            if record is None:
                raise KeyError(f"Reproducibility record not found: {current_id}")
            result.append(record)
            current_id = record.parent_run_id
        return result


def _configuration_hash(configuration: dict[str, Any]) -> str:
    canonical = json.dumps(configuration, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
