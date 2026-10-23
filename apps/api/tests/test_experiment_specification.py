from uuid import uuid4

import pytest
from pydantic import ValidationError

from packages.execution.researchos_execution.experiment import (
    ExperimentSpecification,
    ExperimentSpecificationStore,
)


def specification() -> ExperimentSpecification:
    return ExperimentSpecification(
        research_question="Does longer follow-up improve prediction?",
        hypothesis_id=uuid4(),
        dataset_id="dataset-1",
        split={"strategy": "subject", "train": 0.7, "validation": 0.15, "test": 0.15},
        preprocessing=["standardize numeric features"],
        model={"name": "logistic_regression", "parameters": {"C": 1.0}},
        baselines=[{"name": "majority_class"}],
        metrics=["auroc", "calibration_error"],
        statistics={"confidence_interval": "bootstrap", "alpha": 0.05},
        seeds=[7, 42],
        resources={"cpu": 2, "memory_mb": 4096, "timeout_seconds": 600},
        success_criteria=["AUROC exceeds baseline by 0.05"],
    )


@pytest.mark.asyncio
async def test_experiment_specification_is_validated_and_versioned() -> None:
    store = ExperimentSpecificationStore()

    version = await store.create(specification())

    assert version.version == 1
    assert version.specification.metrics == ["auroc", "calibration_error"]
    assert version.specification.seeds == [7, 42]


def test_experiment_specification_requires_split_and_metric() -> None:
    missing_split = specification().model_dump()
    missing_split["split"] = {}
    with pytest.raises(ValidationError):
        ExperimentSpecification(**missing_split)
    missing_metrics = specification().model_dump()
    missing_metrics["metrics"] = []
    with pytest.raises(ValidationError):
        ExperimentSpecification(**missing_metrics)


def test_success_criteria_must_reference_declared_metric() -> None:
    vague_specification = specification().model_dump()
    vague_specification["success_criteria"] = ["model should work better"]

    with pytest.raises(ValidationError):
        ExperimentSpecification(**vague_specification)


@pytest.mark.asyncio
async def test_new_specification_version_does_not_mutate_previous_version() -> None:
    store = ExperimentSpecificationStore()
    first = await store.create(specification())
    second = await store.create(
        specification().model_copy(update={"experiment_id": first.specification.experiment_id})
    )

    assert first.version == 1
    assert second.version == 2
    stored_first = await store.get(first.specification.experiment_id, 1)
    assert first.specification.model_dump() == stored_first.specification.model_dump()
