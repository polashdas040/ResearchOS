# Projects And Conversations API

All endpoints require:

```http
Authorization: Bearer <access_token>
```

Project, conversation, and message access is scoped to the authenticated
user's primary organization. Inaccessible resources return `404` so object IDs
cannot be probed across organizations.

## Projects

`POST /projects`

```json
{
  "name": "ADNI",
  "description": "Alzheimer disease imaging cohort"
}
```

`GET /projects?limit=50&offset=0`

Returns paginated projects for the current organization.

`GET /projects/{id}`

Returns one project if it belongs to the current organization.

`PATCH /projects/{id}`

```json
{
  "name": "ADNI MRI",
  "description": "Updated scope"
}
```

## Conversations

`POST /projects/{id}/conversations`

```json
{
  "title": "Hypothesis notes"
}
```

`GET /projects/{id}/conversations?limit=50&offset=0`

Returns paginated non-deleted conversations for a project.

`GET /conversations/{id}?limit=50&offset=0`

Returns the conversation and a paginated message page.

`DELETE /conversations/{id}`

Soft deletes the conversation.

## Messages

`POST /conversations/{id}/messages`

```json
{
  "message_type": "USER",
  "content": "Find related work"
}
```

Supported message types:

- `USER`
- `ASSISTANT`
- `SYSTEM_EVENT`
- `TOOL_EVENT`

Tool traces should use `TOOL_EVENT`, not fake assistant messages.
