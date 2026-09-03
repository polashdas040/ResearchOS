from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ColumnKind(StrEnum):
    NUMERIC = "NUMERIC"
    CATEGORICAL = "CATEGORICAL"
    TEXT = "TEXT"


class ColumnStats(BaseModel):
    model_config = ConfigDict(frozen=True)

    mean: float
    minimum: float
    maximum: float


class ColumnProfile(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    kind: ColumnKind
    missing_count: int = Field(ge=0)
    missing_fraction: float = Field(ge=0.0, le=1.0)
    distinct_count: int = Field(ge=0)
    summary_statistics: ColumnStats | None = None
    class_balance: dict[str, int] | None = None
    outlier_count: int = Field(default=0, ge=0)


class CorrelationProfile(BaseModel):
    model_config = ConfigDict(frozen=True)

    left_column: str
    right_column: str
    pearson_r: float


class LongitudinalProfile(BaseModel):
    model_config = ConfigDict(frozen=True)

    subject_count: int = Field(ge=0)
    visits_per_subject: dict[str, int]
    visit_intervals: dict[str, list[float]]
    missing_visits: dict[str, list[float]]
    follow_up_duration: dict[str, float]


class DatasetProfile(BaseModel):
    model_config = ConfigDict(frozen=True)

    dataset_name: str
    row_count: int = Field(ge=0)
    column_count: int = Field(ge=0)
    columns: dict[str, ColumnProfile]
    duplicate_row_count: int = Field(ge=0)
    correlations: list[CorrelationProfile] = Field(default_factory=list)
    potential_leakage: list[str] = Field(default_factory=list)
    longitudinal: LongitudinalProfile | None = None
