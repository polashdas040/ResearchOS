from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ExperimentSpecification(BaseModel):
    model_config = ConfigDict(frozen=True)

    experiment_id: UUID = Field(default_factory=uuid4)
    research_question: str = Field(min_length=1)
    hypothesis_id: UUID
    dataset_id: str = Field(min_length=1)
    split: dict[str, Any] = Field(min_length=1)
    preprocessing: list[str] = Field(min_length=1)
    model: dict[str, Any] = Field(min_length=1)
    baselines: list[dict[str, Any]] = Field(min_length=1)
    metrics: list[str] = Field(min_length=1)
    statistics: dict[str, Any] = Field(min_length=1)
    seeds: list[int] = Field(min_length=1)
    resources: dict[str, Any] = Field(min_length=1)
    success_criteria: list[str] = Field(min_length=1)

    @field_validator("split")
    @classmethod
    def validate_split(cls, value: dict[str, Any]) -> dict[str, Any]:
        required_keys = {"strategy", "train", "validation", "test"}
        missing = required_keys - value.keys()
        if missing:
            raise ValueError(f"split is missing required fields: {', '.join(sorted(missing))}")
        return value

    @model_validator(mode="after")
    def validate_success_criteria_reference_metrics(self) -> "ExperimentSpecification":
        normalized_metrics = {metric.lower() for metric in self.metrics}
        for criterion in self.success_criteria:
            normalized_criterion = criterion.lower()
            if any(metric in normalized_criterion for metric in normalized_metrics):
                continue
            raise ValueError("success criteria must reference at least one declared metric")
        return self


class ExperimentSpecificationVersion(BaseModel):
    model_config = ConfigDict(frozen=True)

    specification: ExperimentSpecification
    version: int = Field(ge=1)


class ExperimentSpecificationStore:
    def __init__(self) -> None:
        self._versions: dict[UUID, list[ExperimentSpecificationVersion]] = {}

    async def create(
        self,
        specification: ExperimentSpecification,
    ) -> ExperimentSpecificationVersion:
        versions = self._versions.setdefault(specification.experiment_id, [])
        version = ExperimentSpecificationVersion(
            specification=specification,
            version=len(versions) + 1,
        )
        versions.append(version)
        return version

    async def get(
        self,
        experiment_id: UUID,
        version: int,
    ) -> ExperimentSpecificationVersion:
        versions = self._versions.get(experiment_id, [])
        if version < 1 or version > len(versions):
            raise KeyError(f"Experiment specification version not found: {experiment_id}/{version}")
        return versions[version - 1]
