# BuildBuddy project memory

## Completed

- Python LangGraph CLI: Planner → Architect → Coder.
- Groq configuration and restricted generated-file tools.
- React + TypeScript/Vite frontend in `frontend/`.
- Responsive landing page, model selector, attachment picker, review section, and footer.
- FastAPI backend under `api/` with modular router design (`health`, `generations`).
- Dynamic `ContextVar` workspace scoping for tools (`safe_path_for_project`, `read_file`, `write_file`, `list_files`, `run_cmd`) per UUID generation run.
- Background agent execution runner (`runner.py`) with lifecycle events (`queued → planning → architecting → coding → completed`).
- REST and SSE streaming endpoints (`/api/generations`, `/api/generations/{id}/events`, `/api/generations/{id}/files`, `/api/generations/{id}/download`, `/api/generations/{id}/cancel`).
- Backend unit and integration test suite passing with `pytest` (100% pass rate across 6 test specs).
- Phase 3 (Part 1 — Code & API Integration Layer):
  - Vite dev proxy configured in `vite.config.ts` mapping `/api` to `http://127.0.0.1:8000`.
  - TypeScript model interfaces created in `types.ts`.
  - API client module created in `api.ts` with typed methods (`createGeneration`, `getGeneration`, `getFileTree`, `getFileContent`, `cancelGeneration`, `getDownloadUrl`, `subscribeToEvents`).
- Phase 3 (Part 2 — UI Layout, Visual & Interactive Workspace Integration):
  - Created interactive loading screen (`LoadingScreen.tsx`) displaying real-time SSE stage events, progress indicator, and active job cancellation button (`onCancel`).
  - Implemented completed stage UI matching user wireframe specification (`ProjectWorkspace.tsx`):
    - Top header bar featuring Logo, "BuildBuddy" brand text, Project Name badge, Download .ZIP action, "＋ Start New Project" action, and rightmost User Profile text avatar (`user-profile-avatar`).
    - Vertically divided resizable 2-container layout (default 35% left container, 65% right container) with interactive drag gutter handle (`resizer-gutter`).
    - Left container: header badge for `Project name` + repository tree explorer (`FileTree.tsx`) with scrollbar for files.
    - Right container: header badges for `Filename` and `Language`, copy code action, edit mode toggle, line numbers gutter, real-time code editor (`CodeViewer.tsx`), and custom scrollbar for code editor.
  - Backend job cancellation support: created `.cancelled` file marker mechanism in `generation_service.py` and `runner.py`, guarded by `check_cancellation_active()` in `agent/tools.py` and graph nodes.
  - Implemented Self-Healing LLM Retry Loop in `planner_agent` and `architect_agent` (up to 3 auto-correction attempts before declaring failure).
  - Optimized code generation speed in `coder_agent` with direct 1-pass LLM code generation and `.invoke({...})` tool calls, reducing generation waiting time to ~10-15s.
  - Implemented Failed Generation Incident Ticket (`LoadingScreen.tsx`) with ticket badge, human-understandable error messages, collapsible raw diagnostics, subdued glass button styling (`.retry-btn`), and CTAs (`Try Again`, `Return to Home`, `Diagnostic Logs`).
  - Implemented Bottom-Right Snackbar Toast component (`SnackbarToast.tsx`) with animated horizontal progress countdown line for API notices, rate limits, and token warnings.
  - Bound `Enter` key on prompt textarea for instant form submission (`Shift+Enter` for multiline) and cleaned URL hash routing (`clearUrlHash()`).
  - Synchronized all repository documentation (`README.md`, `PRD.md`, `architecture.md`, `design.md`, `memory.md`, `phases.md`, `rules.md`).
  - Enhanced Architect & Coder LLM agent prompts in `agent/prompts.py` to produce rich, modular multi-file architectures (HTML, CSS modules, JS modules, animation controllers, data files) for complex prompts and enforce scrollable-container layout specifications (`html, body { height: 100vh; overflow: hidden; }` + container scrolling).
  - Fixed `.workspace-view-root` in `frontend/src/styles.css` with `height: 100vh; max-height: 100vh; overflow: hidden;` so the browser page scrollbar is eliminated and only the Workspace panel containers scroll.
  - Implemented Thread-Based AI Workspace Refinement Engine (`POST /api/generations/{id}/refine` & `refine_project_agent`) for incremental file edits and file creation directly in workspace.
  - Added AI Edit Prompt Panel, scrollable chat message feed, non-overlapping flexbox layout constraints, and message action toolbars (`📋 Copy`, `🔄 Regenerate`, `✏️ Edit`) in `ProjectWorkspace.tsx`.
  - Implemented Persistent URL Routing (`#/project/{id}`) and back/forward browser navigation support.
- Phase 4A Database & Persistence Foundation:
  - Added SQLAlchemy 2.x, Alembic, and Psycopg binary dependencies to pyproject.toml.
  - Configured database foundation in `api/db/` (`base.py`, `session.py`, `models/`, `repositories/`) and `DATABASE_URL` in `api/config.py`.
  - Defined full tenancy ORM schema across 11 tables (`users`, `organizations`, `memberships`, `projects`, `generations`, `generation_events`, `thread_messages`, `project_snapshots`, `artifacts`, `attachments`, `audit_logs`).
  - Created initial Alembic migration (`c26c10eac071_create_core_tenancy_schema.py`) and verified repeatable upgrade/downgrade cycles.
  - Implemented data access repositories (`ProjectRepository`, `GenerationRepository`, `EventRepository`, `MessageRepository`, `SnapshotRepository`, `ArtifactRepository`).
  - Refactored `GenerationService` to persist generation records, lifecycle events, and refinement thread messages directly to SQLite via repositories, eliminating in-memory `_runs` and `meta.json` disk caches while preserving 100% of Pydantic response contracts and frontend compatibility.
  - Backend test suite passing with 100% pass rate across 10 test specs.

## Current limitations

- LangChain debug logging enabled in `agent/graph.py` which can be noisy for production.
- Background jobs run in local asyncio tasks rather than durable worker queues (Redis + ARQ).

## Immediate next task

Phase 4A continuation:
1. Apply ownership and authorization checks to every generation, refinement, file, artifact, event, and download operation.
2. Select one durable queue architecture (Redis + ARQ or Redis + Celery), document the decision, and move generation execution into workers.
3. Add object-storage abstraction and snapshot manifests; do not add frontend authentication until the backend tenancy model is enforced.

## Agent guidance

Read `rules.md`, `architecture.md`, and the relevant `design.md` section before work. Never expose provider keys or raw server paths. Update this file when milestones, limitations, or next work change.
Always proceed step by step. If a prerequisite or setup step is needed before implementation (e.g. package installations, environment variables, external services), break at that exact point of implementation without skipping it, provide the exact steps to the user, and wait for confirmation before writing implementation code.
