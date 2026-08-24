# ResearchOS PLAN 00 Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the initial ResearchOS monorepo and local development foundation with API, web, worker, infrastructure, tests, documentation, and CI.

**Architecture:** Replace the obsolete single-app scaffold with a monorepo rooted at `apps/`, `packages/`, `infra/`, `migrations/`, `docs/`, and `scripts/`. Keep the API thin with only `/health` and `/ready`, put configuration and infrastructure checks behind typed Python modules, and keep the web and worker as minimal runnable shells for later phases.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, pydantic-settings, SQLAlchemy, Alembic, asyncpg, httpx, pytest, pytest-asyncio, Ruff, MyPy, Next.js, React, TypeScript, Tailwind, PostgreSQL, Redis, ChromaDB, MinIO, Docker Compose.

**Spec:** User-provided ResearchOS master roadmap, PLAN 00.

## Global Constraints

- Implement PLAN 00 only.
- Do not implement auth, projects, conversations, files, agents, RAG, billing, or domain entities beyond package placeholders.
- Write failing tests before production implementation.
- Keep API routes thin.
- Use typed Python throughout the backend.
- Use Pydantic models at system boundaries.
- Use Alembic for database migrations.
- PostgreSQL is the authoritative application database.
- Redis, ChromaDB, and object storage are infrastructure dependencies, not sources of application truth.
- Use environment variables and typed settings.
- Do not leave TODO/TBD/pass placeholders.
- Every expensive or external dependency check must be optional in unit tests.
- Commit the phase as `chore: initialize ResearchOS platform`.

---

### Task 1: Replace Obsolete Scaffold With Monorepo Structure

**Files:**
- Delete: `app.py`
- Delete: `backend/__init__.py`
- Delete: `backend/memory.py`
- Delete: `backend/schemas.py`
- Delete: `backend/store.py`
- Delete: `tests/test_memory.py`
- Delete: `tests/test_store.py`
- Delete: `web/app.js`
- Delete: `web/index.html`
- Delete: `web/styles.css`
- Delete: `requirements.txt`
- Delete: `pytest.ini`
- Create: `apps/api/app/__init__.py`
- Create: `apps/api/app/main.py`
- Create: `apps/api/tests/__init__.py`
- Create: `apps/worker/app/__init__.py`
- Create: `packages/core/researchos_core/__init__.py`
- Create: `packages/agents/researchos_agents/__init__.py`
- Create: `packages/rag/researchos_rag/__init__.py`
- Create: `packages/documents/researchos_documents/__init__.py`
- Create: `packages/execution/researchos_execution/__init__.py`
- Create: `packages/evidence/researchos_evidence/__init__.py`
- Create: `packages/memory/researchos_memory/__init__.py`
- Create: `packages/tools/researchos_tools/__init__.py`
- Create: `packages/billing/researchos_billing/__init__.py`
- Create: `packages/observability/researchos_observability/__init__.py`

**Interfaces:**
- Consumes: no runtime interfaces.
- Produces: importable package roots for API, worker, and future shared packages.

- [ ] **Step 1: Write the failing import test**

Create `apps/api/tests/test_package_layout.py`:

```python
from apps.api.app.main import app


def test_api_app_imports() -> None:
    assert app.title == "ResearchOS API"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest apps/api/tests/test_package_layout.py -q`
Expected: FAIL because `apps.api.app.main` does not exist yet.

- [ ] **Step 3: Replace scaffold and add minimal API app**

Delete the obsolete scaffold files and create:

```python
from fastapi import FastAPI


app = FastAPI(title="ResearchOS API")
```

Use empty `__init__.py` files for package roots.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest apps/api/tests/test_package_layout.py -q`
Expected: PASS.

### Task 2: Add Typed Settings And Health Endpoint

**Files:**
- Create: `apps/api/app/config.py`
- Create: `apps/api/app/api/__init__.py`
- Create: `apps/api/app/api/routers/__init__.py`
- Create: `apps/api/app/api/routers/health.py`
- Modify: `apps/api/app/main.py`
- Test: `apps/api/tests/test_health.py`
- Test: `apps/api/tests/test_config.py`
- Create: `pyproject.toml`

**Interfaces:**
- Consumes: environment variables with `RESEARCHOS_` prefix.
- Produces: `Settings`, `get_settings()`, `GET /health`, and `HealthResponse`.

- [ ] **Step 1: Write failing health and settings tests**

Create `apps/api/tests/test_health.py`:

```python
from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_health_returns_ok() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

Create `apps/api/tests/test_config.py`:

```python
from apps.api.app.config import Settings


def test_settings_reads_environment_prefix(monkeypatch) -> None:
    monkeypatch.setenv("RESEARCHOS_ENVIRONMENT", "test")
    monkeypatch.setenv("RESEARCHOS_DATABASE_URL", "postgresql+asyncpg://user:pass@db:5432/researchos")

    settings = Settings()

    assert settings.environment == "test"
    assert str(settings.database_url).startswith("postgresql+asyncpg://")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest apps/api/tests/test_health.py apps/api/tests/test_config.py -q`
Expected: FAIL because `config.py` and `/health` do not exist yet.

- [ ] **Step 3: Add minimal production code**

Create `Settings` with `pydantic-settings`, create a Pydantic `HealthResponse`, register the health router in `main.py`, and add a root `pyproject.toml` with runtime and test dependencies.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest apps/api/tests/test_health.py apps/api/tests/test_config.py -q`
Expected: PASS.

### Task 3: Add Readiness Checks And Alembic Foundation

**Files:**
- Create: `apps/api/app/services/__init__.py`
- Create: `apps/api/app/services/readiness.py`
- Modify: `apps/api/app/api/routers/health.py`
- Create: `apps/api/tests/test_ready.py`
- Create: `apps/api/app/db/__init__.py`
- Create: `apps/api/app/db/base.py`
- Create: `apps/api/app/db/session.py`
- Create: `migrations/env.py`
- Create: `migrations/script.py.mako`
- Create: `migrations/versions/.gitkeep`
- Create: `alembic.ini`

**Interfaces:**
- Consumes: `Settings` URLs for PostgreSQL, Redis, ChromaDB, and object storage.
- Produces: `ReadinessChecker.check() -> ReadinessReport` and `GET /ready`.

- [ ] **Step 1: Write failing readiness test**

Create `apps/api/tests/test_ready.py`:

```python
from fastapi.testclient import TestClient

from apps.api.app.main import app
from apps.api.app.services.readiness import DependencyStatus, ReadinessReport, get_readiness_checker


class PassingChecker:
    async def check(self) -> ReadinessReport:
        return ReadinessReport(
            status="ok",
            dependencies={
                "postgres": DependencyStatus(status="ok"),
                "redis": DependencyStatus(status="ok"),
                "object_storage": DependencyStatus(status="ok"),
            },
        )


def test_ready_returns_ok_when_dependencies_pass() -> None:
    app.dependency_overrides[get_readiness_checker] = lambda: PassingChecker()
    try:
        response = TestClient(app).get("/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest apps/api/tests/test_ready.py -q`
Expected: FAIL because `services.readiness` and `/ready` do not exist.

- [ ] **Step 3: Add readiness and Alembic code**

Implement Pydantic readiness models, a checker with async dependency check methods, the `/ready` route, SQLAlchemy async engine/session helpers, empty metadata base, and Alembic configuration.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest apps/api/tests/test_ready.py -q`
Expected: PASS.

### Task 4: Add Worker And Web Foundations

**Files:**
- Create: `apps/worker/app/main.py`
- Create: `apps/worker/tests/__init__.py`
- Create: `apps/worker/tests/test_worker_import.py`
- Create: `apps/web/package.json`
- Create: `apps/web/next.config.mjs`
- Create: `apps/web/tsconfig.json`
- Create: `apps/web/postcss.config.mjs`
- Create: `apps/web/tailwind.config.ts`
- Create: `apps/web/src/app/globals.css`
- Create: `apps/web/src/app/layout.tsx`
- Create: `apps/web/src/app/page.tsx`
- Create: `apps/web/src/app/page.test.tsx`
- Create: `apps/web/src/test/setup.ts`
- Create: `apps/web/vitest.config.ts`
- Create: root `package.json`

**Interfaces:**
- Consumes: no backend API beyond later expected `/health`.
- Produces: worker import entrypoint and a minimal Next.js ResearchOS shell.

- [ ] **Step 1: Write failing worker and web tests**

Create `apps/worker/tests/test_worker_import.py`:

```python
from apps.worker.app.main import worker_name


def test_worker_name() -> None:
    assert worker_name() == "ResearchOS Worker"
```

Create `apps/web/src/app/page.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import Page from "./page";

it("renders the ResearchOS foundation shell", () => {
  render(<Page />);
  expect(screen.getByRole("heading", { name: "ResearchOS" })).toBeInTheDocument();
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest apps/worker/tests/test_worker_import.py -q`
Expected: FAIL because `apps.worker.app.main` does not exist.

Run after Node dependencies are installed: `npm --workspace apps/web test -- --runInBand`
Expected: FAIL because the web app files do not exist.

- [ ] **Step 3: Add minimal worker and web app**

Implement `worker_name() -> str`, a Next.js App Router page, Tailwind setup, and Vitest testing setup.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest apps/worker/tests/test_worker_import.py -q`
Expected: PASS.

Run after Node dependencies are installed: `npm --workspace apps/web test -- --runInBand`
Expected: PASS.

### Task 5: Add Local Development Infrastructure, Commands, CI, And Docs

**Files:**
- Create: `docker-compose.yml`
- Create: `infra/docker/api.Dockerfile`
- Create: `infra/docker/web.Dockerfile`
- Create: `infra/docker/worker.Dockerfile`
- Create: `infra/nginx/.gitkeep`
- Create: `infra/postgres/.gitkeep`
- Create: `infra/redis/.gitkeep`
- Create: `infra/chroma/.gitkeep`
- Create: `infra/monitoring/.gitkeep`
- Create: `scripts/dev.ps1`
- Create: `Makefile`
- Create: `.env.example`
- Create: `.github/workflows/ci.yml`
- Create: `README.md`
- Create: `CODEX_MASTER_PROMPT.md`
- Create: `docs/architecture/plan-00-foundation.md`
- Create: `docs/api/health.md`
- Create: `docs/adr/0001-monorepo-foundation.md`

**Interfaces:**
- Consumes: root Python and Node project files from previous tasks.
- Produces: `make dev`, `make test`, `make lint`, `make format`, `make migrate`, and `make migration` command targets plus documented local startup.

- [ ] **Step 1: Write failing command smoke test**

Create `apps/api/tests/test_project_files.py`:

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def test_required_foundation_files_exist() -> None:
    required = [
        "docker-compose.yml",
        "Makefile",
        ".env.example",
        ".github/workflows/ci.yml",
        "README.md",
        "CODEX_MASTER_PROMPT.md",
        "docs/architecture/plan-00-foundation.md",
        "docs/api/health.md",
        "docs/adr/0001-monorepo-foundation.md",
    ]

    missing = [path for path in required if not (ROOT / path).exists()]

    assert missing == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest apps/api/tests/test_project_files.py -q`
Expected: FAIL because the foundation files do not exist.

- [ ] **Step 3: Add infrastructure, command, CI, and documentation files**

Create Docker Compose services for `api`, `web`, `worker`, `postgres`, `redis`, `chroma`, and `minio`. Add a Makefile whose targets call Python, Alembic, Ruff, MyPy, Pytest, and npm workspace commands. Add CI that installs Python and Node dependencies, then runs lint and tests.

- [ ] **Step 4: Run full verification**

Run:

```bash
pytest -q
ruff check .
mypy apps packages
npm --workspace apps/web test -- --runInBand
npm --workspace apps/web lint
```

Expected: all commands pass.

- [ ] **Step 5: Commit PLAN 00**

Run:

```bash
git add .
git commit -m "chore: initialize ResearchOS platform"
```

Expected: commit succeeds and no next roadmap phase begins.

## Self-Review

### Spec coverage
- Monorepo layout: Task 1.
- Python workspace: Tasks 1, 2, and 3.
- Node workspace and Next.js app: Task 4.
- FastAPI app: Tasks 1, 2, and 3.
- Worker app: Task 4.
- PostgreSQL, Redis, ChromaDB, and object storage: Task 5.
- Docker Compose: Task 5.
- Configuration, logging, linting, formatting, testing, CI: Tasks 2, 3, and 5.
- Alembic migrations: Task 3.
- Health and ready endpoints: Tasks 2 and 3.
- Documentation and master prompt: Task 5.

### Placeholder scan
- No TODO, TBD, or pass placeholders are used.
- Every task includes concrete files, tests, commands, and expected results.

### Type consistency
- `Settings`, `HealthResponse`, `DependencyStatus`, `ReadinessReport`, and `ReadinessChecker.check()` are named before downstream use.
- Test import paths match the planned monorepo package paths.
