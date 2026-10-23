import math
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field


class StatisticalReviewRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    values: list[float] = Field(min_length=2)
    baseline_values: list[float] | None = None
    confidence_level: float = Field(default=0.95, gt=0.0, lt=1.0)
    paired: bool = False
    comparison_count: int = Field(default=1, ge=1)
    independent_samples: bool = True


class StatisticalSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    count: int = Field(ge=2)
    mean: float
    standard_deviation: float = Field(ge=0.0)
    confidence_interval: tuple[float, float]


class PairedComparison(BaseModel):
    model_config = ConfigDict(frozen=True)

    count: int = Field(ge=2)
    mean_difference: float
    effect_size: float


class StatisticalReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    summary: StatisticalSummary
    comparison: PairedComparison | None = None
    warnings: list[str] = Field(default_factory=list)
    reproducible: bool


class StatisticalReviewer:
    _Z_SCORES: ClassVar[dict[float, float]] = {
        0.90: 1.6448536269514722,
        0.95: 1.959963984540054,
        0.99: 2.5758293035489004,
    }

    async def review(self, request: StatisticalReviewRequest) -> StatisticalReport:
        if request.confidence_level not in self._Z_SCORES:
            supported = ", ".join(str(level) for level in sorted(self._Z_SCORES))
            raise ValueError(f"unsupported confidence level; supported values are {supported}")
        if request.paired and request.baseline_values is None:
            raise ValueError("paired comparison requires baseline values")
        if request.paired and len(request.values) != len(request.baseline_values or []):
            raise ValueError("paired samples must have the same length")
        summary = _summary(request.values, request.confidence_level, self._Z_SCORES)
        comparison = None
        if request.baseline_values is not None:
            if len(request.baseline_values) < 2:
                raise ValueError("baseline requires at least two values")
            if request.paired:
                comparison = _paired_comparison(request.values, request.baseline_values)
        warnings: list[str] = []
        if request.comparison_count > 1:
            warnings.append("Multiple comparisons require correction or adjusted interpretation.")
        if not request.independent_samples:
            warnings.append(
                "Independence assumption is not satisfied; use paired or clustered analysis."
            )
        return StatisticalReport(
            summary=summary,
            comparison=comparison,
            warnings=warnings,
            reproducible=True,
        )


def _summary(
    values: list[float],
    confidence_level: float,
    z_scores: dict[float, float],
) -> StatisticalSummary:
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    standard_deviation = math.sqrt(variance)
    z_score = z_scores[confidence_level]
    margin = z_score * standard_deviation / math.sqrt(len(values))
    return StatisticalSummary(
        count=len(values),
        mean=mean,
        standard_deviation=standard_deviation,
        confidence_interval=(mean - margin, mean + margin),
    )


def _paired_comparison(values: list[float], baseline_values: list[float]) -> PairedComparison:
    differences = [
        value - baseline for value, baseline in zip(values, baseline_values, strict=True)
    ]
    mean_difference = sum(differences) / len(differences)
    variance = sum((difference - mean_difference) ** 2 for difference in differences) / (
        len(differences) - 1
    )
    standard_deviation = math.sqrt(variance)
    effect_size = mean_difference / standard_deviation if standard_deviation else 0.0
    return PairedComparison(
        count=len(differences),
        mean_difference=mean_difference,
        effect_size=effect_size,
    )
