from uuid import uuid4

import pytest

from packages.execution.researchos_execution.experiment_runner import (
    ExperimentRun,
    ExperimentRunStatus,
)
from packages.execution.researchos_execution.reproducibility import (
    ReproducibilityLedger,
)


def run() -> ExperimentRun:
    return ExperimentRun(
        experiment_id=uuid4(),
        status=ExperimentRunStatus.SUCCEEDED,
        code_commit="abc123",
        dataset_fingerprint="sha256:dataset",
        environment={"python": "3.12", "package": "1.0"},
        hardware={"cpu": "2"},
        configuration={"model": "baseline", "metric": "auroc"},
        seed=42,
        metrics={"auroc": 0.84},
        logs="complete",
        output_artifacts=["artifact://output"],
    )


@pytest.mark.asyncio
async def test_ledger_records_complete_immutable_provenance() -> None:
    ledger = ReproducibilityLedger()
    experiment_run = run()

    record = await ledger.record(
        experiment_run,
        input_artifacts=["artifact://input"],
    )

    assert record.run_id == experiment_run.id
    assert record.dataset_fingerprint == "sha256:dataset"
    assert record.code_commit == "abc123"
    assert len(record.configuration_hash) == 64
    assert record.input_artifacts == ["artifact://input"]
    assert record.output_artifacts == ["artifact://output"]
    assert (await ledger.get(experiment_run.id)) == record


@pytest.mark.asyncio
async def test_ledger_lineage_is_traversable_and_hash_is_reproducible() -> None:
    ledger = ReproducibilityLedger()
    parent = run()
    child = run()
    parent_record = await ledger.record(parent, input_artifacts=[])
    child_record = await ledger.record(
        child,
        input_artifacts=[],
        parent_run_id=parent.id,
    )

    assert child_record.configuration_hash == parent_record.configuration_hash
    lineage = await ledger.lineage(child.id)
    assert [record.run_id for record in lineage] == [child.id, parent.id]


@pytest.mark.asyncio
async def test_ledger_rejects_unknown_parent_run() -> None:
    ledger = ReproducibilityLedger()

    with pytest.raises(KeyError, match="Parent reproducibility record"):
        await ledger.record(run(), input_artifacts=[], parent_run_id=uuid4())
