# PLAN 02 Projects And Persistent Conversations

PLAN 02 adds tenant-scoped projects, conversations, and messages.

## Scope

- Projects are owned by an organization and record the creating user.
- Conversations belong to projects.
- Messages belong to conversations and keep explicit message type.
- Conversation deletion is a soft delete.
- List endpoints support `limit` and `offset` pagination.
- API routes require the current authenticated user.
- Cross-organization access returns `404`.

## Architecture

Routes translate HTTP requests and responses, then delegate to
`ProjectService`. `ProjectService` applies tenant scoping with the authenticated
user's primary organization and raises a single resource-not-found error for
missing or inaccessible data. `ProjectRepository` hides persistence details.

The default repository is `SqlAlchemyProjectRepository`, backed by PostgreSQL.
Tests inject `InMemoryProjectRepository` for route-level isolation and use a
separate SQLite-backed repository test for persistence behavior.

## Tables

- `projects`
- `conversations`
- `messages`

The Alembic migration is
`migrations/versions/20260825_0002_projects_conversations.py`.

## Security Notes

Frontend-provided project and conversation IDs are never trusted alone. Every
read or write includes the authenticated user's organization in the repository
query. Returning `404` for inaccessible resources avoids disclosing whether an
object exists in another organization.
