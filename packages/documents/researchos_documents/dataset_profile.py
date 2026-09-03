import csv
import math
from collections import Counter, defaultdict
from io import StringIO

from apps.api.app.domain.datasets.models import (
    ColumnKind,
    ColumnProfile,
    ColumnStats,
    CorrelationProfile,
    DatasetProfile,
    LongitudinalProfile,
)


class CsvDatasetProfiler:
    def profile(self, csv_text: str, dataset_name: str) -> DatasetProfile:
        rows = list(csv.DictReader(StringIO(csv_text)))
        fieldnames = list(rows[0].keys()) if rows else []
        columns = {
            name: _profile_column(name, [row.get(name, "") or "" for row in rows])
            for name in fieldnames
        }
        return DatasetProfile(
            dataset_name=dataset_name,
            row_count=len(rows),
            column_count=len(fieldnames),
            columns=columns,
            duplicate_row_count=_duplicate_count(rows, fieldnames),
            correlations=_correlations(columns, rows),
            potential_leakage=_leakage_hints(fieldnames),
            longitudinal=_longitudinal_profile(rows, fieldnames),
        )


def _profile_column(name: str, values: list[str]) -> ColumnProfile:
    present = [value.strip() for value in values if value.strip() != ""]
    missing_count = len(values) - len(present)
    numeric_values = [_to_float(value) for value in present]
    numeric_present = [value for value in numeric_values if value is not None]
    kind = _column_kind(present, numeric_present)
    summary = _stats(numeric_present) if kind == ColumnKind.NUMERIC else None
    class_balance = dict(Counter(present)) if kind == ColumnKind.CATEGORICAL else None
    return ColumnProfile(
        name=name,
        kind=kind,
        missing_count=missing_count,
        missing_fraction=round(missing_count / len(values), 4) if values else 0.0,
        distinct_count=len(set(present)),
        summary_statistics=summary,
        class_balance=class_balance,
        outlier_count=_outlier_count(numeric_present),
    )


def _column_kind(present: list[str], numeric_present: list[float]) -> ColumnKind:
    if present and len(numeric_present) == len(present):
        return ColumnKind.NUMERIC
    if len(set(present)) <= max(20, len(present) // 2):
        return ColumnKind.CATEGORICAL
    return ColumnKind.TEXT


def _stats(values: list[float]) -> ColumnStats | None:
    if not values:
        return None
    return ColumnStats(
        mean=round(sum(values) / len(values), 4),
        minimum=min(values),
        maximum=max(values),
    )


def _duplicate_count(rows: list[dict[str, str]], fieldnames: list[str]) -> int:
    seen: set[tuple[str, ...]] = set()
    duplicates = 0
    for row in rows:
        signature = tuple(row.get(name, "") for name in fieldnames)
        if signature in seen:
            duplicates += 1
        seen.add(signature)
    return duplicates


def _correlations(
    columns: dict[str, ColumnProfile],
    rows: list[dict[str, str]],
) -> list[CorrelationProfile]:
    numeric_columns = [
        name for name, profile in columns.items() if profile.kind == ColumnKind.NUMERIC
    ]
    correlations: list[CorrelationProfile] = []
    for left_index, left in enumerate(numeric_columns):
        for right in numeric_columns[left_index + 1 :]:
            pairs = [
                (left_value, right_value)
                for row in rows
                if (left_value := _to_float(row.get(left, ""))) is not None
                and (right_value := _to_float(row.get(right, ""))) is not None
            ]
            if len(pairs) >= 2:
                r = _pearson([pair[0] for pair in pairs], [pair[1] for pair in pairs])
                if abs(r) >= 0.75:
                    correlations.append(
                        CorrelationProfile(
                            left_column=left,
                            right_column=right,
                            pearson_r=round(r, 4),
                        )
                    )
    return correlations


def _leakage_hints(fieldnames: list[str]) -> list[str]:
    hints: list[str] = []
    lower_to_original = {name.lower(): name for name in fieldnames}
    for lower, original in lower_to_original.items():
        if lower.startswith("target_"):
            source = lower.removeprefix("target_")
            if source in lower_to_original:
                hints.append(f"{original} may leak {lower_to_original[source]}")
    return hints


def _longitudinal_profile(
    rows: list[dict[str, str]],
    fieldnames: list[str],
) -> LongitudinalProfile | None:
    if "subject_id" not in fieldnames or "visit_month" not in fieldnames:
        return None
    visits: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        subject_id = row.get("subject_id", "").strip()
        visit = _to_float(row.get("visit_month", ""))
        if subject_id and visit is not None:
            visits[subject_id].append(visit)
    if not visits:
        return None
    sorted_visits = {subject: sorted(set(values)) for subject, values in visits.items()}
    all_visits = sorted({visit for values in sorted_visits.values() for visit in values})
    return LongitudinalProfile(
        subject_count=len(sorted_visits),
        visits_per_subject={subject: len(values) for subject, values in sorted_visits.items()},
        visit_intervals={
            subject: [
                round(values[index] - values[index - 1], 4)
                for index in range(1, len(values))
            ]
            for subject, values in sorted_visits.items()
        },
        missing_visits={
            subject: [visit for visit in all_visits if visit not in values]
            for subject, values in sorted_visits.items()
            if [visit for visit in all_visits if visit not in values]
        },
        follow_up_duration={
            subject: round(values[-1] - values[0], 4) for subject, values in sorted_visits.items()
        },
    )


def _outlier_count(values: list[float]) -> int:
    if len(values) < 4:
        return 0
    sorted_values = sorted(values)
    q1 = sorted_values[len(sorted_values) // 4]
    q3 = sorted_values[(len(sorted_values) * 3) // 4]
    iqr = q3 - q1
    if iqr == 0:
        return 0
    low = q1 - 1.5 * iqr
    high = q3 + 1.5 * iqr
    return sum(1 for value in values if value < low or value > high)


def _pearson(left: list[float], right: list[float]) -> float:
    left_mean = sum(left) / len(left)
    right_mean = sum(right) / len(right)
    numerator = sum((a - left_mean) * (b - right_mean) for a, b in zip(left, right, strict=True))
    left_denominator = math.sqrt(sum((value - left_mean) ** 2 for value in left))
    right_denominator = math.sqrt(sum((value - right_mean) ** 2 for value in right))
    if left_denominator == 0 or right_denominator == 0:
        return 0.0
    return numerator / (left_denominator * right_denominator)


def _to_float(value: str | None) -> float | None:
    if value is None or value.strip() == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None
