from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from packages.execution.researchos_execution.experiment import ExperimentSpecification


class ExperimentRunStatus(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class ExperimentExecutionResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: ExperimentRunStatus
    metrics: dict[str, float] = Field(default_factory=dict)
    logs: str = ""
    output_artifacts: list[str] = Field(default_factory=list)
    error: str | None = None


class ExperimentRun(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    experiment_id: UUID
    status: ExperimentRunStatus
    code_commit: str = Field(min_length=1)
    dataset_fingerprint: str = Field(min_length=1)
    environment: dict[str, Any] = Field(min_length=1)
    hardware: dict[str, Any] = Field(min_length=1)
    configuration: dict[str, Any] = Field(min_length=1)
    seed: int
    metrics: dict[str, float]
    logs: str
    output_artifacts: list[str]
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ExperimentExecutor(Protocol):
    async def execute(
        self,
        experiment: ExperimentSpecification,
        code: str,
        seed: int,
    ) -> ExperimentExecutionResult: ...


class ExperimentRunStore:
    def __init__(self) -> None:
        self._runs: dict[UUID, list[ExperimentRun]] = {}

    async def create(self, run: ExperimentRun) -> ExperimentRun:
        self._runs.setdefault(run.experiment_id, []).append(run)
        return run

    async def list_runs(self, experiment_id: UUID) -> list[ExperimentRun]:
        return list(self._runs.get(experiment_id, []))


class ExperimentRunner:
    def __init__(self, executor: ExperimentExecutor, store: ExperimentRunStore) -> None:
        self._executor = executor
        self._store = store

    async def run(
        self,
        specification: ExperimentSpecification,
        code: str,
        code_commit: str,
        dataset_fingerprint: str,
        environment: dict[str, Any],
        hardware: dict[str, Any],
        seed: int,
    ) -> ExperimentRun:
        if seed not in specification.seeds:
            raise ValueError("experiment run seed must be declared in the specification")
        execution = await self._executor.execute(specification, code, seed)
        run = ExperimentRun(
            experiment_id=specification.experiment_id,
            status=execution.status,
            code_commit=code_commit,
            dataset_fingerprint=dataset_fingerprint,
            environment=dict(environment),
            hardware=dict(hardware),
            configuration=specification.model_dump(mode="json"),
            seed=seed,
            metrics=dict(execution.metrics),
            logs=execution.logs,
            output_artifacts=list(execution.output_artifacts),
            error=execution.error,
        )
        return await self._store.create(run)
