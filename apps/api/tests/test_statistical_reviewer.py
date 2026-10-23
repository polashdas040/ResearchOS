import math

import pytest

from packages.agents.researchos_agents.statistical_reviewer import (
    StatisticalReviewer,
    StatisticalReviewRequest,
)


@pytest.mark.asyncio
async def test_statistical_reviewer_computes_reproducible_uncertainty_and_effect_size() -> None:
    report = await StatisticalReviewer().review(
        StatisticalReviewRequest(
            values=[0.80, 0.82, 0.78, 0.84],
            baseline_values=[0.70, 0.72, 0.71, 0.73],
            confidence_level=0.95,
            paired=True,
        )
    )

    assert report.summary.count == 4
    assert math.isclose(report.summary.mean, 0.81)
    assert report.summary.confidence_interval[0] < report.summary.mean
    assert report.summary.confidence_interval[1] > report.summary.mean
    assert report.comparison is not None
    assert report.comparison.mean_difference > 0
    assert report.comparison.effect_size > 0
    assert report.reproducible is True


@pytest.mark.asyncio
async def test_statistical_reviewer_reports_multiple_comparison_and_independence_warnings() -> None:
    report = await StatisticalReviewer().review(
        StatisticalReviewRequest(
            values=[1.0, 2.0, 3.0],
            confidence_level=0.90,
            paired=False,
            comparison_count=5,
            independent_samples=False,
        )
    )

    assert any("multiple comparisons" in warning.lower() for warning in report.warnings)
    assert any("independence" in warning.lower() for warning in report.warnings)


@pytest.mark.asyncio
async def test_statistical_reviewer_rejects_mismatched_paired_samples() -> None:
    with pytest.raises(ValueError, match="same length"):
        await StatisticalReviewer().review(
            StatisticalReviewRequest(
                values=[1.0, 2.0],
                baseline_values=[1.0],
                paired=True,
            )
        )


@pytest.mark.asyncio
async def test_statistical_reviewer_rejects_unsupported_confidence_level() -> None:
    with pytest.raises(ValueError, match="confidence level"):
        await StatisticalReviewer().review(
            StatisticalReviewRequest(
                values=[1.0, 2.0, 3.0],
                confidence_level=0.975,
            )
        )
