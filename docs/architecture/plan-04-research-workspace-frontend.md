# PLAN 04: Research Workspace Frontend

PLAN 04 introduces the first real ResearchOS workspace interface while keeping the data static. Backend client wiring, file uploads, and autonomous research runtime behavior belong to later phases.

## Routes

- `/`: workspace entry page with links to sign in and open the demo workspace.
- `/login`: login form shell.
- `/register`: registration form shell.
- `/projects`: project list shell.
- `/project/[id]`: ChatGPT-style research workspace.
- `/settings`: account/workspace settings shell.
- `/billing`: credit and usage shell.

## Components

The project workspace is composed from focused components in `apps/web/src/components`:

- `AppHeader`
- `ProjectSidebar`
- `ConversationSidebar`
- `ChatThread`
- `StreamingMessage`
- `MessageComposer`
- `FileAttachment`
- `ResearchRunPanel`
- `ArtifactPanel`
- `WorkspaceShell`

## UI Boundary

This phase intentionally uses deterministic fixture data from `workspace-data.ts`. The frontend displays:

- projects
- conversations
- chat messages
- file attachment control
- run progress
- artifact list
- settings and billing shells

It does not yet authenticate against the API, stream live SSE tokens, upload files, or mutate server state.

## Privacy

The workspace shows task/run status and observable results only. It does not expose hidden model reasoning or private chain-of-thought.
