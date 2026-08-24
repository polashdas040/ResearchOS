# Research Chat + Memory Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first working version of the new research platform: a chat-first multi-agent backend with persistent thread history and ChromaDB-backed memory.

**Architecture:** Keep the backend provider-neutral and split it into small services: HTTP API, thread store, memory index, and research orchestration. The frontend should be a chat workspace that loads prior conversations and can grow later into login, credits, PDF ingestion, and multimodal reading without a rewrite.

**Tech Stack:** FastAPI, Uvicorn, Pydantic, ChromaDB, React or a similarly maintainable chat frontend, pytest, python-dotenv.

**Spec:** `docs/superpowers/specs/2026-08-24-multi-agent-research-platform-design.md`

## Global Constraints

- Phase 1 scope only: chat-first research workspace, persistent history, and retrieval memory.
- ChromaDB is the retrieval layer; the relational store remains the source of truth for threads and messages.
- The backend must log full tracebacks to the terminal on failures.
- The UI must stay light, readable, and non-dark.
- The system must stay provider-neutral so the LLM backend can be swapped later.

---

### Task 1: Backend Contracts and Thread Store

**Files:**
- Modify: `app.py`
- Create: `backend/__init__.py`
- Create: `backend/schemas.py`
- Create: `backend/store.py`
- Create: `tests/test_store.py`

**Interfaces:**
- Consumes: raw chat input from HTTP requests and a user/thread identifier.
- Produces: `ChatMessage`, `ChatThread`, and `ThreadStore` with `load()`, `save()`, `append_message()`, and `get_thread()` methods.

- [ ] **Step 1: Write the failing test**

```python
from backend.store import ThreadStore


def test_thread_store_persists_messages(tmp_path):
    path = tmp_path / "threads.json"
    store = ThreadStore(path)
    store.append_message("guest", "user", "Hello")
    store.append_message("guest", "assistant", "Hi there")

    reloaded = ThreadStore(path)
    reloaded.load()

    thread = reloaded.get_thread("guest")
    assert [m.content for m in thread.messages] == ["Hello", "Hi there"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_store.py -v`
Expected: FAIL because `backend.store` and `ThreadStore` do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
from dataclasses import dataclass, field
from pathlib import Path
import json


@dataclass
class ChatMessage:
    role: str
    content: str


@dataclass
class ChatThread:
    user_id: str
    messages: list[ChatMessage] = field(default_factory=list)


class ThreadStore:
    def __init__(self, path: Path):
        self.path = path
        self.threads: dict[str, ChatThread] = {}

    def load(self) -> None:
        ...

    def save(self) -> None:
        ...

    def append_message(self, user_id: str, role: str, content: str) -> ChatThread:
        ...

    def get_thread(self, user_id: str) -> ChatThread:
        ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_store.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app.py backend/schemas.py backend/store.py tests/test_store.py
git commit -m "feat: add thread store contracts"
```

### Task 2: ChromaDB Memory Index

**Files:**
- Create: `backend/memory.py`
- Create: `tests/test_memory.py`

**Interfaces:**
- Consumes: a thread id, text chunks, and query text.
- Produces: `MemoryHit` objects and a `MemoryIndex` with `add_texts()` and `search()` methods.

- [ ] **Step 1: Write the failing test**

```python
from backend.memory import MemoryIndex


def test_memory_index_returns_relevant_chunk(tmp_path):
    index = MemoryIndex(tmp_path / "chroma")
    index.add_texts(
        thread_id="guest",
        texts=[
            "LLM agents use planning and tools.",
            "Bananas are yellow.",
        ],
    )

    hits = index.search("How do LLM agents use tools?", thread_id="guest", k=1)
    assert hits[0].text == "LLM agents use planning and tools."
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_memory.py -v`
Expected: FAIL because `backend.memory` and `MemoryIndex` do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
from dataclasses import dataclass


@dataclass
class MemoryHit:
    text: str
    metadata: dict[str, str]
    score: float | None = None


class MemoryIndex:
    def __init__(self, persist_dir):
        ...

    def add_texts(self, thread_id: str, texts: list[str]) -> None:
        ...

    def search(self, query: str, thread_id: str, k: int = 3) -> list[MemoryHit]:
        ...
```

Use a deterministic embedder in tests so the results do not depend on network access.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_memory.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/memory.py tests/test_memory.py
git commit -m "feat: add chroma memory index"
```

### Task 3: Multi-Agent Research Orchestrator

**Files:**
- Create: `backend/agents.py`
- Create: `backend/research_service.py`
- Create: `tests/test_research_service.py`

**Interfaces:**
- Consumes: `user_id`, `message`, thread history, and memory hits.
- Produces: a structured `ResearchResult` with `reply`, `sources`, `memory_hits`, and `trace`.

- [ ] **Step 1: Write the failing test**

```python
from backend.research_service import ResearchService


def test_service_includes_memory_and_sources(monkeypatch):
    service = ResearchService(
        search_fn=lambda q: ["https://example.com"],
        reader_fn=lambda url: "example source text",
        synthesizer_fn=lambda prompt: "final answer",
    )

    result = service.run(user_id="guest", message="Tell me about LLM agents")
    assert result.reply == "final answer"
    assert result.sources == ["https://example.com"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_research_service.py -v`
Expected: FAIL because `ResearchService` does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
from dataclasses import dataclass, field


@dataclass
class ResearchResult:
    reply: str
    sources: list[str] = field(default_factory=list)
    memory_hits: list[str] = field(default_factory=list)
    trace: list[str] = field(default_factory=list)


class ResearchService:
    def __init__(self, search_fn, reader_fn, synthesizer_fn, memory_index=None):
        ...

    def run(self, user_id: str, message: str) -> ResearchResult:
        ...
```

The orchestrator should ask the memory index first, then perform search, then read, then synthesize.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_research_service.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/agents.py backend/research_service.py tests/test_research_service.py
git commit -m "feat: add research orchestrator"
```

### Task 4: ChatGPT-Like Chat Workspace

**Files:**
- Create or modify the frontend app files needed for a ChatGPT-like layout.
- Include a left sidebar, a central message stream, and a pinned bottom composer.
- Create tests for the main layout.

**Interfaces:**
- Consumes: `/api/chat` and `/api/history/{user_id}`.
- Produces: a chat workspace with a thread sidebar, message timeline, and memory/source side panel.

- [ ] **Step 1: Write the failing test**

```jsx
import { render, screen } from "@testing-library/react";
import App from "./App";


test("renders the research workspace", () => {
  render(<App />);
  expect(screen.getByText("Research Agent Studio")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- --runInBand`
Expected: FAIL because the chat workspace is not implemented yet.

- [ ] **Step 3: Write minimal implementation**

```jsx
export default function App() {
  return (
    <main>
      <h1>Research Agent Studio</h1>
      <section>Chat</section>
      <section>Stored history</section>
    </main>
  );
}
```

The UI should be light, ChatGPT-like in structure, and reusable for later uploads and memory panels.

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- --runInBand`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/package.json frontend/index.html frontend/vite.config.js frontend/src
git commit -m "feat: add chat workspace shell"
```

### Task 5: API Wiring and End-to-End Verification

**Files:**
- Modify: `app.py`
- Create: `tests/test_api.py`
- Create: `scripts/run_dev.ps1`

**Interfaces:**
- Consumes: backend services from Tasks 1-3 and the chat workspace from Task 4.
- Produces: a running app that serves the frontend and answers chat/history requests end to end.

- [ ] **Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient
from app import app


def test_chat_endpoint_returns_reply():
    client = TestClient(app)
    response = client.post("/api/chat", json={"user_id": "guest", "message": "Hello"})
    assert response.status_code == 200
    assert "reply" in response.json()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_api.py -v`
Expected: FAIL until the backend wiring is complete.

- [ ] **Step 3: Write minimal implementation**

Wire `app.py` to the backend services, mount the frontend build output, and return structured errors for bad requests.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_api.py -v`
Expected: PASS.

- [ ] **Step 5: Smoke test the app**

Run:
```bash
python app.py
```

Expected:
- server starts without import errors
- `/api/chat` returns a reply
- history is persisted across restarts

- [ ] **Step 6: Commit**

```bash
git add app.py tests/test_api.py scripts/run_dev.ps1
git commit -m "feat: wire chat app end to end"
```

## Self-Review

### Spec coverage
- Research chat core: Task 3 and Task 4.
- Persistent conversation history: Task 1 and Task 5.
- ChromaDB memory: Task 2.
- Provider-neutral orchestration: Task 3.
- Light, non-dark UI: Task 4.
- Terminal traceback logging and structured API errors: Task 5.

### Placeholder scan
- No TBD/TODO placeholders.
- Every test step includes a concrete test file and command.
- Every implementation step names concrete classes and methods.

### Type consistency
- `ThreadStore`, `ChatThread`, and `ChatMessage` are defined before they are used by later tasks.
- `MemoryIndex` and `MemoryHit` are introduced before the orchestrator consumes them.
- `ResearchService` and `ResearchResult` are defined before the API task wires them in.

