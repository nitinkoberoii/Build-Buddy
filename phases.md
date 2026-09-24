# BuildBuddy delivery phases

## Phase 0 — agent foundation (complete)

- LangGraph Planner → Architect → Coder flow.
- Groq-backed CLI execution and scoped output tools.

## Phase 1 — web foundation (complete)

- React, TypeScript, and Vite frontend.
- Responsive product landing experience and design system.

## Phase 2 — API foundation (complete)

- FastAPI application and typed schemas.
- Reusable generation service extracted from CLI.
- UUID-scoped run storage and lifecycle events.
- Health, create, status, event, files, download, and cancel endpoints.
- Unit/API tests and OpenAPI documentation.

**Exit criterion met:** an API client can start a run, observe state, cancel if needed, and safely access output files.

## Phase 3 — frontend workflow (complete)

- **Part 1 (Complete)**: API client (`api.ts`), TypeScript schemas (`types.ts`), Vite dev proxy (`vite.config.ts`), and SSE event subscription handlers.
- **Part 2 (Complete)**: UI visual layout, progress dashboard with live terminal log and cancellation (`LoadingScreen.tsx`), file tree explorer (`FileTree.tsx`), code viewer (`CodeViewer.tsx`), and project workspace UI (`ProjectWorkspace.tsx`).

**Exit criterion met:** a browser user can submit a prompt, monitor progress, cancel active runs, inspect generated code, and download a project without a terminal.

## Phase 4 — reliability (next / in progress)

- Background jobs, timeout/cancel policy, logs, metrics, rate limits, CORS, and input/file validation.
- SQLite local persistence, PostgreSQL deployment migration, object-storage artifacts.
- End-to-end tests and CI.

## Phase 5 — launch and iteration

- Authentication, user history, retention, deployment, monitoring, user feedback, and model quality evaluation.

