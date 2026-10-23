from dataclasses import dataclass

import pytest
from pydantic import ValidationError

from apps.api.tests.test_experiment_specification import specification
from packages.execution.researchos_execution.experiment import ExperimentSpecification
from packages.execution.researchos_execution.experiment_runner import (
    ExperimentExecutionResult,
    ExperimentRun,
    ExperimentRunner,
    ExperimentRunStatus,
    ExperimentRunStore,
)


@dataclass
class FakeExecutor:
    results: list[ExperimentExecutionResult]
    received_specs: list[ExperimentSpecification]

    async def execute(
        self,
        experiment: ExperimentSpecification,
        code: str,
        seed: int,
    ) -> ExperimentExecutionResult:
        self.received_specs.append(experiment)
        return self.results.pop(0)


@pytest.mark.asyncio
async def test_experiment_runner_persists_independent_runs_and_provenance() -> None:
    store = ExperimentRunStore()
    executor = FakeExecutor(
        results=[
            ExperimentExecutionResult(
                status=ExperimentRunStatus.SUCCEEDED,
                metrics={"auroc": 0.84},
                logs="finished",
                output_artifacts=["artifact://result-1"],
            ),
            ExperimentExecutionResult(
                status=ExperimentRunStatus.SUCCEEDED,
                metrics={"auroc": 0.86},
                logs="finished",
                output_artifacts=["artifact://result-2"],
            ),
        ],
        received_specs=[],
    )
    runner = ExperimentRunner(executor, store)
    experiment = specification()

    first = await runner.run(
        experiment,
        code="print('run')",
        code_commit="abc123",
        dataset_fingerprint="sha256:dataset",
        environment={"python": "3.12"},
        hardware={"cpu": "2"},
        seed=7,
    )
    second = await runner.run(
        experiment,
        code="print('run')",
        code_commit="abc123",
        dataset_fingerprint="sha256:dataset",
        environment={"python": "3.12"},
        hardware={"cpu": "2"},
        seed=42,
    )

    assert first.id != second.id
    assert first.status == ExperimentRunStatus.SUCCEEDED
    assert first.seed == 7
    assert first.dataset_fingerprint == "sha256:dataset"
    assert first.output_artifacts == ["artifact://result-1"]
    assert len(await store.list_runs(first.experiment_id)) == 2
    assert second.metrics["auroc"] == 0.86


@pytest.mark.asyncio
async def test_experiment_runner_persists_failed_run_without_mutating_prior_runs() -> None:
    store = ExperimentRunStore()
    executor = FakeExecutor(
        results=[
            ExperimentExecutionResult(
                status=ExperimentRunStatus.FAILED,
                metrics={},
                logs="ValueError",
                output_artifacts=[],
                error="ValueError",
            )
        ],
        received_specs=[],
    )

    run = await ExperimentRunner(executor, store).run(
        specification(),
        code="raise ValueError",
        code_commit="def456",
        dataset_fingerprint="sha256:dataset-2",
        environment={"python": "3.12"},
        hardware={"cpu": "2"},
        seed=7,
    )

    assert run.status == ExperimentRunStatus.FAILED
    assert run.error == "ValueError"
    assert run.logs == "ValueError"


@pytest.mark.asyncio
async def test_experiment_runner_rejects_seed_not_declared_in_specification() -> None:
    store = ExperimentRunStore()
    executor = FakeExecutor(
        results=[
            ExperimentExecutionResult(
                status=ExperimentRunStatus.SUCCEEDED,
                metrics={"auroc": 0.8},
            )
        ],
        received_specs=[],
    )

    with pytest.raises(ValueError, match="declared"):
        await ExperimentRunner(executor, store).run(
            specification(),
            code="print('run')",
            code_commit="abc123",
            dataset_fingerprint="sha256:dataset",
            environment={"python": "3.12"},
            hardware={"cpu": "2"},
            seed=999,
        )

    assert executor.received_specs == []


def test_experiment_run_requires_reproducibility_metadata() -> None:
    with pytest.raises(ValidationError):
        ExperimentRun(
            experiment_id=specification().experiment_id,
            status=ExperimentRunStatus.SUCCEEDED,
            code_commit="",
            dataset_fingerprint="sha256:dataset",
            environment={"python": "3.12"},
            hardware={"cpu": "2"},
            configuration={"model": "demo"},
            seed=7,
            metrics={"auroc": 0.9},
            logs="ok",
            output_artifacts=[],
        )
