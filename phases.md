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

## Phase 3 — frontend workflow & interactive workspace (complete)

- **Part 1 (Complete)**: API client (`api.ts`), TypeScript schemas (`types.ts`), Vite dev proxy (`vite.config.ts`), and SSE event subscription handlers.
- **Part 2 (Complete)**:
  - Progress dashboard with live terminal log and job cancellation (`LoadingScreen.tsx`).
  - Resizable split container layout (35% left container for file tree explorer, 65% right container for code editor).
  - Syntax-highlighted code editor with line numbers, copy button, and inline edit mode (`CodeViewer.tsx`).
  - Header bar with logo, brand text, project name badge, download ZIP CTA, start new project button, and user profile avatar (`NK`).
  - Self-healing LLM retry loop in agent planner and architect nodes (up to 3 auto-corrections).
  - Fast 1-pass LLM direct file generation (~10–15s total generation time).
  - Failed generation Incident Ticket UI (`TICKET #BB-FAIL-XXXXXXXX`) with human-readable error descriptions, raw log toggle, and subdued glass action buttons (`Try Again`, `Return to Home`).
  - Bottom-right snackbar toast notifications (`SnackbarToast.tsx`) with animated shrinking progress countdown line.
  - Keyboard submission binding (`Enter` key on prompt textarea).
  - Thread-Based AI Workspace Refinement Engine (`POST /api/generations/{id}/refine` & `refine_project_agent`) for incremental file updates and file creation.
  - Interactive AI edit prompt panel below file tree with scrollable thread message log (`ThreadMessage`), non-overlapping flexbox layout, and message action toolbars (`📋 Copy`, `🔄 Regenerate`, `✏️ Edit`).
  - Persistent URL Hash & Path Routing (`#/project/{id}`) enabling page reloads (`F5`), direct link sharing, and back/forward browser navigation support.

**Exit criterion met:** a browser user can submit a prompt (via click or `Enter`), monitor progress, cancel active runs, inspect generated code in a resizable split workspace, perform incremental AI file edits within a thread session, reload/bookmark workspaces via persistent URLs, recover gracefully from generation errors via incident tickets, receive transient API/token notices, and download a project without a terminal.

## Phase 4 — reliability (next / in progress)

- Background jobs, timeout/cancel policy, logs, metrics, rate limits, CORS, and input/file validation.
- SQLite local persistence, PostgreSQL deployment migration, object-storage artifacts.
- End-to-end tests and CI.

## Phase 5 — launch and iteration

- Authentication, user history, retention, deployment, monitoring, user feedback, and model quality evaluation.

