# BuildBuddy project memory

## Completed

- Python LangGraph CLI: Planner → Architect → Coder.
- Groq configuration and restricted generated-file tools.
- React + TypeScript/Vite frontend in `frontend/`.
- Responsive landing page, model selector, attachment picker, review section, and footer.
- Frontend `npm run build` passes.
- Project architecture, design, PRD, phase, and rule documents exist.

## Current limitations

- Backend is CLI-only: no HTTP APIs.
- Frontend controls are local/presentational only.
- One shared `generated_project-todo/` output directory is unsafe for concurrent web use.
- No database, authentication, run history, status streaming, or artifact archive.
- LangChain debug logging is enabled and unsuitable for production.

## Immediate next task

Build API foundation before further landing-page work:

1. Add FastAPI under `api/` or `server/`.
2. Extract reusable generation execution from CLI code.
3. Create one UUID-scoped output directory per run.
4. Implement health, creation, status, event, file-list/read, and download routes.
5. Connect the prompt form to creation and build a generation-progress route.

## Agent guidance

Read `rules.md`, `architecture.md`, and the relevant `design.md` section before work. Never expose provider keys or raw server paths. Update this file when milestones, limitations, or next work change.
