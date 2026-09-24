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
  - Created project workspace component (`ProjectWorkspace.tsx`) featuring an interactive file tree explorer (`FileTree.tsx`), live syntax-highlighted code viewer (`CodeViewer.tsx`), and single-click project ZIP archive downloader.
  - Backend job cancellation support: created `.cancelled` file marker mechanism in `generation_service.py` and `runner.py`, guarded by `check_cancellation_active()` in `agent/tools.py` and graph nodes.
  - Verified full end-to-end user workflow from prompt submission to live progress, cancellation handling, file exploration, and ZIP export.
- Project architecture, design, PRD, phase, and rule documents exist.

## Current limitations

- In-memory event stream queues and run storage; need persistent SQLite/PostgreSQL database storage for multi-instance production scale (Phase 4).
- LangChain debug logging enabled in `agent/graph.py` which can be noisy for production.

## Immediate next task

Phase 4 (Reliability & Persistence):

1. Implement SQLite local database persistence for runs and events in `storage/`.
2. Implement task runner timeout policies, background queue management, rate limits, and CORS configuration.
3. Add end-to-end integration tests and CI pipeline configuration.

## Agent guidance

Read `rules.md`, `architecture.md`, and the relevant `design.md` section before work. Never expose provider keys or raw server paths. Update this file when milestones, limitations, or next work change.

