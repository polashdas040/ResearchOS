from apps.api.app.domain.datasets.models import ColumnKind
from packages.documents.researchos_documents.dataset_profile import CsvDatasetProfiler


def test_csv_profile_reports_shape_types_missingness_duplicates_and_stats() -> None:
    csv_text = "\n".join(
        [
            "subject_id,visit_month,label,age,score,target_score",
            "S1,0,case,70,10,20",
            "S1,12,case,71,12,24",
            "S2,0,control,68,8,16",
            "S2,0,control,68,8,16",
            "S3,0,case,,15,30",
        ]
    )

    profile = CsvDatasetProfiler().profile(csv_text, dataset_name="cohort.csv")

    assert profile.dataset_name == "cohort.csv"
    assert profile.row_count == 5
    assert profile.column_count == 6
    assert profile.duplicate_row_count == 1
    assert profile.columns["age"].kind == ColumnKind.NUMERIC
    assert profile.columns["age"].missing_count == 1
    assert profile.columns["age"].missing_fraction == 0.2
    assert profile.columns["label"].class_balance == {"case": 3, "control": 2}
    assert profile.columns["score"].summary_statistics is not None
    assert profile.columns["score"].summary_statistics.mean == 10.6
    assert "target_score may leak score" in profile.potential_leakage


def test_csv_profile_detects_longitudinal_subject_visits() -> None:
    csv_text = "\n".join(
        [
            "subject_id,visit_month,value",
            "S1,0,1.0",
            "S1,6,1.5",
            "S1,12,1.8",
            "S2,0,2.0",
            "S2,12,2.4",
        ]
    )

    profile = CsvDatasetProfiler().profile(csv_text, dataset_name="longitudinal.csv")

    assert profile.longitudinal is not None
    assert profile.longitudinal.subject_count == 2
    assert profile.longitudinal.visits_per_subject == {"S1": 3, "S2": 2}
    assert profile.longitudinal.visit_intervals == {"S1": [6.0, 6.0], "S2": [12.0]}
    assert profile.longitudinal.missing_visits == {"S2": [6.0]}
    assert profile.longitudinal.follow_up_duration == {"S1": 12.0, "S2": 12.0}


def test_csv_profile_reports_correlations_and_outliers() -> None:
    csv_text = "\n".join(
        [
            "x,y",
            "1,2",
            "2,4",
            "3,6",
            "4,8",
            "100,200",
        ]
    )

    profile = CsvDatasetProfiler().profile(csv_text, dataset_name="correlated.csv")

    assert profile.correlations[0].left_column == "x"
    assert profile.correlations[0].right_column == "y"
    assert profile.correlations[0].pearson_r == 1.0
    assert profile.columns["x"].outlier_count == 1
