# PLAN 03: Chat Streaming and Model Gateway

PLAN 03 introduces the first model boundary without coupling application code directly to any external SDK.

## Boundaries

- API routes remain thin and only handle request validation, authentication dependencies, and SSE response formatting.
- `ChatStreamingService` owns the application workflow for persisted user messages, model streaming, assistant message persistence, provider failure handling, and usage recording.
- `ModelGateway` and model protocols live in `apps/api/app/services/model_gateway.py`.
- `UsageRepository` records model usage events. PostgreSQL is the authoritative store; in-memory repositories are test-only.

## Event Flow

```text
Browser
  -> POST /conversations/{id}/messages/stream
  -> authenticated principal
  -> tenant-scoped conversation lookup
  -> persisted USER message
  -> ModelGateway.chat_model().stream(...)
  -> SSE message.delta events
  -> persisted ASSISTANT message
  -> model_usage_events row
  -> SSE message.completed event
```

Provider failures emit `message.failed` and do not persist partial assistant content.

## Usage

Usage is stored in `model_usage_events` with organization, project, conversation, optional assistant message, provider, model, and token counts. This is intentionally separate from the future credit ledger.

## Current Limitation

The default model is deterministic and local. PLAN 03 establishes the provider abstraction and streaming contract; production provider configuration, frontend streaming UI, billing, and agent runtime behavior belong to later phases.
