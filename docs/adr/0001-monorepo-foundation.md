# ADR 0001: Monorepo Foundation

## Status

Accepted

## Context

ResearchOS needs coordinated API, web, worker, infrastructure, and shared package development. Later phases will add authentication, persistent projects, document processing, retrieval, agents, experiments, billing, observability, and deployment.

## Decision

Use one monorepo with `apps/` for runnable services, `packages/` for shared libraries, `infra/` for local infrastructure, `migrations/` for Alembic, and `docs/` for architecture and API decisions.

PostgreSQL is the authoritative transactional database. Redis is coordination infrastructure. ChromaDB is retrieval infrastructure. MinIO provides S3-compatible object storage in local development.

## Consequences

The repository starts slightly broader than a single FastAPI app, but future roadmap phases can add behavior without moving core directories or collapsing infrastructure concerns into routes.
