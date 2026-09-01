# Job API

PLAN 06 adds durable background job records. PostgreSQL stores job history and status; Redis remains coordination infrastructure, not authoritative history.

## Endpoints

- `POST /jobs`
  - Creates a tenant-scoped queued job.
  - Body fields: `job_type`, `payload`, optional `max_attempts`, optional `idempotency_key`.
  - Supported initial job types: `DOCUMENT_PARSE`, `EMBED_DOCUMENT`, `RESEARCH_RUN`, `DATASET_PROFILE`, `EXPERIMENT`.

- `GET /jobs/{job_id}`
  - Returns job status, attempts, result, error, and timestamps.
  - Jobs are only visible inside the authenticated user's organization.

## Statuses

Jobs use `QUEUED`, `RUNNING`, `SUCCEEDED`, `FAILED`, `RETRYING`, and `CANCELLED`.
