# PLAN 06 Durable Jobs

PLAN 06 introduces the durable job substrate used by document parsing, embedding, research runs, dataset profiling, and experiments.

## Design

- `Job` is the domain object.
- `jobs` is the PostgreSQL source of truth.
- `JobRepository` owns persistence.
- `JobService` owns tenant-scoped API use.
- `JobRunner` claims one queued/retrying job and executes a registered handler.

## Retry Behavior

Failed jobs move to `RETRYING` until `attempts` reaches `max_attempts`. The final failed attempt persists `FAILED` and the error text.

## Idempotency

`idempotency_key` is unique per organization. Reusing the same key returns the existing job instead of creating a duplicate.

## Current Limits

Handlers are registered in process for this phase. PLAN 07 and later will add concrete document/data/research handlers.
