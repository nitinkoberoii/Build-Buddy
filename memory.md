# BuildBuddy project memory

## Completed

- Python LangGraph CLI: Planner → Architect → Coder.
- Groq configuration and restricted generated-file tools.
- React + TypeScript/Vite frontend in `frontend/`.
- Responsive landing page, model selector, attachment picker, review section, and footer.
- FastAPI backend under `api/` with modular router design (`health`, `generations`).
- Dynamic `ContextVar` workspace scoping for tools (`safe_path_for_project`, `read_file`, `write_file`, `list_files`, `run_cmd`) per UUID generation run.
- Background agent execution runner (`runner.py`) with lifecycle events (`queued → planning → architecting → coding → completed`).
- REST and SSE streaming endpoints (`/api/generations`, `/api/generations/{id}/events`, `/api/generations/{id}/files`, `/api/generations/{id}/download`).
- Backend unit and integration test suite passing with `pytest` (100% pass rate across 4 test specs).
- Phase 3 (Part 1 — Code & API Integration Layer):
  - Vite dev proxy configured in `vite.config.ts` mapping `/api` to `http://127.0.0.1:8000`.
  - TypeScript model interfaces created in `types.ts`.
  - API client module created in `api.ts` with typed methods (`createGeneration`, `getGeneration`, `getFileTree`, `getFileContent`, `cancelGeneration`, `getDownloadUrl`, `subscribeToEvents`).
  - Frontend build (`npm run build`) verified and passing 100%.
- Project architecture, design, PRD, phase, and rule documents exist.

## Current limitations

- Frontend visual components awaiting Part 2 UI reference design.
- In-memory event stream queues; need persistent database storage for multi-instance production scale.
- LangChain debug logging is enabled and unsuitable for production.

## Immediate next task

Phase 3 (Part 2 — UI Layout & Visual Integration):

1. Receive UI design reference and layout mockups from user.
2. Build real-time generation progress view, terminal event log, file tree explorer, and code viewer components.
3. Wire UI components to `api.ts` data client and test end-to-end user flow.

## Agent guidance

Read `rules.md`, `architecture.md`, and the relevant `design.md` section before work. Never expose provider keys or raw server paths. Update this file when milestones, limitations, or next work change.
