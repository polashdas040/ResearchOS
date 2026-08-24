# ResearchOS

ResearchOS is a production-grade autonomous AI research problem-solving platform. PLAN 00 establishes the development foundation only: API, web shell, worker shell, infrastructure services, tests, linting, migrations, and documentation.

## Local Development

1. Copy `.env.example` to `.env`.
2. Install Python dependencies with `pip install -e ".[dev]"`.
3. Install Node dependencies with `npm install`.
4. Start infrastructure and apps with `make dev`.

## Commands

- `make dev`: start Docker Compose services.
- `make test`: run Python and web tests.
- `make lint`: run Ruff, MyPy, and web lint.
- `make format`: format Python and web code.
- `make migrate`: apply Alembic migrations.
- `make migration message="name"`: create an Alembic migration.

## PLAN 00 Scope

This phase intentionally does not include authentication, projects, chat, files, retrieval, agents, billing, or research runtime behavior.
