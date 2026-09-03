# Dataset Profiles

Dataset profiles summarize uploaded tabular data without sending full datasets to an LLM.

## CSV Scope

`CsvDatasetProfiler` reports row and column counts, inferred column kinds, missingness, duplicate rows, class balance, numeric summary statistics, outlier counts, high correlations, possible leakage hints, and longitudinal visit metadata when `subject_id` and `visit_month` are present.

This phase uses deterministic local parsing. DuckDB or Polars can replace the implementation behind the same profile schema later.
