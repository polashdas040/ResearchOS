from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from apps.api.app.domain.datasets.models import DatasetProfile


class FeasibilityDecision(StrEnum):
    PASS = "PASS"
    PASS_WITH_RISKS = "PASS_WITH_RISKS"
    FAIL = "FAIL"


class FeasibilityRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    dataset_profile: DatasetProfile
    required_columns: list[str] = Field(default_factory=list)
    required_modalities: list[str] = Field(default_factory=list)
    available_modalities: list[str] = Field(default_factory=list)
    minimum_samples: int = Field(default=0, ge=0)
    estimated_compute: float = Field(default=0.0, ge=0.0)
    compute_budget: float = Field(default=0.0, ge=0.0)
    evaluation_available: bool = True
    ethical_constraints: list[str] = Field(default_factory=list)


class FeasibilityResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    decision: FeasibilityDecision
    reasons: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class FeasibilityAgent:
    async def assess(self, request: FeasibilityRequest) -> FeasibilityResult:
        reasons: list[str] = []
        risks: list[str] = []
        recommendations: list[str] = []
        profile = request.dataset_profile
        available_columns = set(profile.columns)
        missing_columns = sorted(set(request.required_columns) - available_columns)
        if missing_columns:
            reasons.append(f"Required columns are missing: {', '.join(missing_columns)}")
            recommendations.append(
                "Acquire or define the missing dataset columns before execution."
            )
        missing_modalities = sorted(
            set(request.required_modalities) - set(request.available_modalities)
        )
        if missing_modalities:
            reasons.append(f"Required modalities are unavailable: {', '.join(missing_modalities)}")
            recommendations.append("Provide the missing modalities or revise the hypothesis scope.")
        if profile.row_count < request.minimum_samples:
            reasons.append(
                f"Dataset has {profile.row_count} samples but requires {request.minimum_samples}."
            )
            recommendations.append("Collect more samples or lower the minimum sample requirement.")
        if request.estimated_compute > request.compute_budget:
            reasons.append(
                "Estimated compute "
                f"{request.estimated_compute} exceeds budget {request.compute_budget}."
            )
            recommendations.append("Increase the compute budget or reduce experiment complexity.")
        if not request.evaluation_available:
            reasons.append("No evaluation procedure or benchmark is available.")
            recommendations.append(
                "Define an evaluation split, metric, and baseline before execution."
            )
        if request.ethical_constraints:
            reasons.extend(
                f"Ethical constraint requires review: {constraint}"
                for constraint in request.ethical_constraints
            )
            recommendations.append("Resolve ethical review requirements before execution.")

        for column_name in request.required_columns:
            column = profile.columns.get(column_name)
            if column is None:
                continue
            if column.missing_fraction >= 1.0:
                reasons.append(f"Required column {column_name} has no observed values.")
                recommendations.append(
                    f"Populate {column_name} or remove it from the experiment requirements."
                )
            elif column.missing_fraction >= 0.2:
                risks.append(
                    "Required column "
                    f"{column_name} has {column.missing_fraction:.0%} missing values."
                )
        if profile.duplicate_row_count > 0:
            risks.append(f"Dataset contains {profile.duplicate_row_count} duplicate rows.")
        risks.extend(f"Potential leakage indicator: {hint}" for hint in profile.potential_leakage)

        if reasons:
            decision = FeasibilityDecision.FAIL
        elif risks:
            decision = FeasibilityDecision.PASS_WITH_RISKS
        else:
            decision = FeasibilityDecision.PASS
        return FeasibilityResult(
            decision=decision,
            reasons=reasons,
            risks=risks,
            recommendations=recommendations,
        )
