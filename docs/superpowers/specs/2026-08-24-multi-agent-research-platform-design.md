# Multi-Agent Research Platform Design

## Goal
Build a research assistant that helps users explore topics deeply through chat, multi-agent reasoning, uploaded documents, and persistent memory. The first release should focus on the research chat core and long-term conversation memory. Later phases will add login, credit-based access, PDF ingestion, table extraction, and image understanding.

## Product Shape
The app will move from a single-run research script into a web-based research workspace:

- A chat-first interface for asking research questions and following the thread deeply.
- A backend API that orchestrates multiple agents for search, reading, synthesis, and critique.
- Persistent user accounts and sessions.
- ChromaDB-backed retrieval for prior chats, uploaded files, and extracted research notes.
- File upload support for PDFs first, then tables and images.

## Phase 1 Scope
Phase 1 is the foundation:

- Chat UI for research conversations.
- Multi-agent backend pipeline.
- Persistent chat history per thread.
- ChromaDB memory for previous conversations and notes.
- Basic source tracking and citations.

This phase does not need full billing or multimodal document intelligence yet.

## Phase 1 Architecture

### Frontend
Use a ChatGPT-like layout for the primary experience:

- left sidebar for threads and memory shortcuts
- central chat stream
- pinned composer at the bottom
- clean light theme
- source and upload tools in a restrained side panel

The implementation may use React or a similarly maintainable frontend structure if it keeps the layout clean and reusable.

### Backend
Use a Python API service instead of a script-first entry point.

Core endpoints:

- `POST /api/auth/login`
- `POST /api/chat`
- `GET /api/threads`
- `GET /api/threads/:id`
- `POST /api/uploads`
- `POST /api/memory/search`

### Agent Layer
Split the reasoning pipeline into dedicated roles:

- Planner agent: breaks the request into sub-questions.
- Search agent: finds current web sources.
- Reader agent: opens and extracts relevant source text.
- Synthesizer agent: writes the answer.
- Critic agent: checks quality and gaps.
- Memory agent: retrieves prior relevant chats and notes.

The agents should communicate through structured data, not free-form text alone.

## Data Flow

1. User submits a question in chat.
2. The backend loads the user thread and relevant memory from ChromaDB.
3. The planner identifies sub-tasks.
4. Search and reader agents gather supporting material.
5. Synthesizer produces the response.
6. Critic produces a quality check and improvement notes.
7. The final response, sources, and metadata are stored.
8. The memory index is updated for future retrieval.

## Storage Design

### Relational Store
Use a relational database for durable application state:

- users
- sessions
- chat threads
- messages
- uploads
- source metadata
- credit ledger
- usage events

### ChromaDB
Use ChromaDB for retrieval-oriented memory:

- prior conversation summaries
- extracted PDF text chunks
- note fragments
- research snippets
- image OCR text later

The relational store remains the system of record. ChromaDB is the retrieval layer.

## Auth And Credits
This is a later phase, but the design should reserve the model now.

Auth requirements:

- login credentials
- password hashing
- user identity tied to threads and uploads
- session persistence across browser restarts

Credits requirements:

- each research run consumes credits
- file uploads can consume separate credits
- the UI shows remaining balance
- the backend refuses actions when credits are exhausted

## PDF, Table, And Image Support

### PDF
The first document format to support will be PDF.

Pipeline:

- upload PDF
- extract text
- chunk text
- store metadata
- embed chunks into ChromaDB
- allow chat to query the document

### Tables
Table support should come after PDF text ingestion.

Expected behavior:

- detect tabular content
- preserve row and column structure where possible
- expose table summaries to the agent pipeline

### Images
Image support is the last multimodal step in the first major expansion.

Expected behavior:

- OCR text extraction
- basic visual description
- link image notes to the chat thread and memory store

## Error Handling

- All backend failures should be logged in the terminal with full tracebacks.
- The API should return structured error messages, not raw stack traces.
- The chat UI should show when the system falls back to partial results.
- Model failures, network failures, and ingestion failures should be separated in logs.

## Testing Strategy

### Backend
- unit tests for agent orchestration
- tests for memory retrieval
- tests for upload ingestion
- tests for credit checks
- tests for auth/session behavior

### Frontend
- render tests for chat, history, and source panels
- interaction tests for send, load history, and upload actions

### Integration
- end-to-end test for login -> chat -> persist -> reload history
- end-to-end test for PDF upload -> retrieval -> answer grounded in file

## Build Order

1. Convert the current app into a stable API + chat shell.
2. Add persistent chat threads and ChromaDB memory.
3. Add login and session storage.
4. Add credit accounting.
5. Add PDF upload and retrieval.
6. Add table extraction.
7. Add image understanding.

## Non-Goals For The First Phase

- full payments integration
- advanced image reasoning
- complex analytics dashboards
- multi-tenant enterprise admin features
- agent marketplace or plugin ecosystem

## Open Choices

- Database engine for the relational store: SQLite for development, then PostgreSQL when the app is ready to scale.
- LLM provider strategy: keep the interface provider-neutral so OpenAI can be swapped or supplemented later.
- File parsing stack: choose libraries based on the first PDF/table ingestion pass.

## Success Criteria

- A user can chat with the assistant and get deep research answers.
- The conversation is persisted and loaded on the next login.
- Relevant past chats are retrieved from memory when a new question is asked.
- The system degrades gracefully when model calls fail.
- The structure is ready for uploads, credits, and multimodal reasoning without a rewrite.

