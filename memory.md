# BuildBuddy project memory

## Completed

- Python LangGraph CLI: Planner → Architect → Coder.
- Groq configuration and restricted generated-file tools.
- React + TypeScript/Vite frontend in `frontend/`.
- Responsive landing page, model selector, attachment picker, review section, and footer.
- Frontend `npm run build` passes.
- FastAPI backend under `api/` with modular router design (`health`, `generations`).
- Dynamic `ContextVar` workspace scoping for tools (`safe_path_for_project`, `read_file`, `write_file`, `list_files`, `run_cmd`) per UUID generation run.
- Background agent execution runner (`runner.py`) with lifecycle events (`queued → planning → architecting → coding → completed`).
- REST and SSE streaming endpoints (`/api/generations`, `/api/generations/{id}/events`, `/api/generations/{id}/files`, `/api/generations/{id}/download`).
- Backend unit and integration test suite passing with `pytest` (100% pass rate across 4 test specs).
- Project architecture, design, PRD, phase, and rule documents exist.

## Current limitations

- Frontend controls are currently local/presentational only and need API integration.
- In-memory event stream queues; need persistent database storage for production scale.
- LangChain debug logging is enabled and unsuitable for production.

## Immediate next task

Phase 3 — Connect Frontend Workflow to API:

1. Wire prompt submission form on landing page to `POST /api/generations`.
2. Implement SSE progress view with stage progress indicators and live event feed.
3. Build file tree explorer and code preview component fed by `/api/generations/{id}/files`.
4. Connect project ZIP download button to `/api/generations/{id}/download`.
5. Add cancellation and error recovery UI states.

## Agent guidance

Read `rules.md`, `architecture.md`, and the relevant `design.md` section before work. Never expose provider keys or raw server paths. Update this file when milestones, limitations, or next work change.
