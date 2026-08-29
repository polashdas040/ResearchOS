# Chat Streaming API

PLAN 03 adds authenticated server-sent event streaming for conversation messages.

## Stream Message

`POST /conversations/{conversation_id}/messages/stream`

Headers:

- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

Body:

```json
{
  "content": "Summarize this research goal"
}
```

Response media type:

`text/event-stream`

Events:

- `message.started`: emitted after the user message is accepted and persisted.
- `message.delta`: emitted for assistant token/content deltas.
- `message.completed`: emitted after the assistant message is persisted and usage is recorded.
- `message.failed`: emitted when the model provider fails. Partial assistant content is not persisted.

Example:

```text
event: message.started
data: {"conversation_id":"...","user_message_id":"..."}

event: message.delta
data: {"delta":"Echo:"}

event: message.completed
data: {"assistant_message_id":"...","usage":{"prompt_tokens":3,"completion_tokens":3,"total_tokens":6}}
```

## Security

The endpoint uses the same bearer authentication and tenant-scoped conversation authorization as the persistent conversation APIs. The frontend cannot provide `user_id`, `organization_id`, or `project_id`; those are derived from the authenticated principal and the authorized conversation.

## Current Provider

The default provider is a deterministic local adapter for development and tests. Real external LLM providers will be added behind the same gateway interface rather than called directly from API routes.
