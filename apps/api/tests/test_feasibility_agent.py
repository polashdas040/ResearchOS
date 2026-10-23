import pytest

from apps.api.app.domain.datasets.models import ColumnKind, ColumnProfile, DatasetProfile
from packages.agents.researchos_agents.feasibility import (
    FeasibilityAgent,
    FeasibilityDecision,
    FeasibilityRequest,
)


def profile(
    *,
    row_count: int = 500,
    missing_fraction: float = 0.0,
    potential_leakage: list[str] | None = None,
) -> DatasetProfile:
    return DatasetProfile(
        dataset_name="cohort",
        row_count=row_count,
        column_count=2,
        columns={
            "outcome": ColumnProfile(
                name="outcome",
                kind=ColumnKind.NUMERIC,
                missing_count=int(row_count * missing_fraction),
                missing_fraction=missing_fraction,
                distinct_count=100,
            ),
            "age": ColumnProfile(
                name="age",
                kind=ColumnKind.NUMERIC,
                missing_count=0,
                missing_fraction=0.0,
                distinct_count=80,
            ),
        },
        duplicate_row_count=0,
        potential_leakage=potential_leakage or [],
    )


@pytest.mark.asyncio
async def test_feasibility_passes_when_data_compute_and_evaluation_are_available() -> None:
    result = await FeasibilityAgent().assess(
        FeasibilityRequest(
            dataset_profile=profile(),
            required_columns=["outcome", "age"],
            required_modalities=["clinical"],
            available_modalities=["clinical"],
            minimum_samples=100,
            estimated_compute=4.0,
            compute_budget=8.0,
            evaluation_available=True,
        )
    )

    assert result.decision == FeasibilityDecision.PASS
    assert result.reasons == []


@pytest.mark.asyncio
async def test_feasibility_returns_pass_with_risks_for_data_quality_warnings() -> None:
    result = await FeasibilityAgent().assess(
        FeasibilityRequest(
            dataset_profile=profile(missing_fraction=0.35, potential_leakage=["visit_id"]),
            required_columns=["outcome"],
            required_modalities=[],
            available_modalities=[],
            minimum_samples=100,
            estimated_compute=1.0,
            compute_budget=8.0,
            evaluation_available=True,
        )
    )

    assert result.decision == FeasibilityDecision.PASS_WITH_RISKS
    assert any("missing" in risk.lower() for risk in result.risks)
    assert any("leakage" in risk.lower() for risk in result.risks)


@pytest.mark.asyncio
async def test_feasibility_fails_when_required_modality_is_missing() -> None:
    result = await FeasibilityAgent().assess(
        FeasibilityRequest(
            dataset_profile=profile(),
            required_columns=["outcome"],
            required_modalities=["imaging"],
            available_modalities=["clinical"],
            minimum_samples=100,
            estimated_compute=1.0,
            compute_budget=8.0,
            evaluation_available=True,
        )
    )

    assert result.decision == FeasibilityDecision.FAIL
    assert any("imaging" in reason for reason in result.reasons)
    assert result.recommendations


@pytest.mark.asyncio
async def test_feasibility_fails_when_a_required_column_has_no_observed_values() -> None:
    result = await FeasibilityAgent().assess(
        FeasibilityRequest(
            dataset_profile=profile(missing_fraction=1.0),
            required_columns=["outcome"],
            minimum_samples=100,
            estimated_compute=1.0,
            compute_budget=8.0,
        )
    )

    assert result.decision == FeasibilityDecision.FAIL
    assert any("no observed values" in reason.lower() for reason in result.reasons)
