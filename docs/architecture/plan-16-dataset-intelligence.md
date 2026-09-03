# PLAN 16 Dataset Intelligence

PLAN 16 adds deterministic CSV profiling for research datasets.

## Decisions

- Dataset profiles are structured Pydantic models.
- The initial profiler uses Python standard library CSV parsing to avoid adding large data dependencies before they are needed.
- The profiler computes statistics locally and never delegates arithmetic or whole-dataset inspection to an LLM.
- Longitudinal summaries are detected from `subject_id` and `visit_month` columns.

Parquet, Excel, persistence, and public API routes are deferred to later dataset workflow phases.
