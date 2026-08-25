# ResearchOS

ResearchOS is a production-grade autonomous AI research problem-solving platform. The current platform includes the development foundation plus PLAN 01 authentication and tenant security.

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

## Implemented Scope

- PLAN 00: API, web shell, worker shell, infrastructure services, tests, linting, migrations, and documentation.
- PLAN 01: users, organizations, memberships, password hashing, bearer tokens, refresh-token rotation, logout, `GET /users/me`, and authorization service.

This project intentionally does not yet include projects, persistent conversations, files, retrieval, agents, billing, or research runtime behavior.
