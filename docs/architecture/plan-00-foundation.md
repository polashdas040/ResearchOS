# PLAN 00 Foundation Architecture

PLAN 00 creates the ResearchOS monorepo and local development foundation.

## Components

- `apps/api`: FastAPI application with `/health` and `/ready`.
- `apps/web`: Next.js workspace shell.
- `apps/worker`: importable worker entrypoint for later durable jobs.
- `packages/*`: importable placeholders for future domain packages.
- `migrations`: Alembic migration environment.
- `infra`: Docker and infrastructure configuration.

## Boundaries

API routes stay thin. Configuration lives in `apps/api/app/config.py`; dependency readiness lives in `apps/api/app/services/readiness.py`; database session setup lives under `apps/api/app/db`.

No authentication, projects, conversations, files, agents, retrieval, billing, or domain entities are implemented in this phase.
