# BuildBuddy architecture

## Goal

BuildBuddy turns a natural-language request into a structured starter project. The web product must submit a prompt, show its progress, expose generated files safely, and allow download without exposing provider credentials.

## Current system

`main.py → LangGraph → Planner → Architect → Coder → generated_project-todo/`

- `agent/graph.py` owns LangGraph and Groq calls.
- `agent/tools.py` supplies restricted generated-project tools.
- `frontend/` is a Vite, React, TypeScript landing experience; it has no API connection.

## Target system

```text
React client
  │ POST /api/generations
  ▼
FastAPI service
  ├── validation, rate limits, auth/session boundary
  ├── generation/run orchestration and status events
  ├── file/archive service
  └── persistence (runs/events/metadata)
  │
  ▼
LangGraph Planner → Architect → Coder
  │
  ▼
Groq or allowlisted LLM provider
```

## MVP API

| Method | Route | Purpose |
| --- | --- | --- |
| `POST` | `/api/generations` | Start a validated generation; return run ID. |
| `GET` | `/api/generations/{id}` | Return state, plan, summary, and errors. |
| `GET` | `/api/generations/{id}/events` | Stream progress with SSE. |
| `GET` | `/api/generations/{id}/files` | List safe generated files. |
| `GET` | `/api/generations/{id}/files/{path}` | Read one validated file. |
| `GET` | `/api/generations/{id}/download` | Download an allowlisted ZIP. |
| `GET` | `/api/health` | Deployment health check. |

## Run states

`queued → planning → architecting → coding → completed`

Terminal states: `completed`, `failed`, `cancelled`, `timed_out`. Every transition creates a timestamped event. A browser can recover after reconnecting by reading the run status.

## Security and storage

- Every run gets a UUID-scoped output folder, never the shared `generated_project-todo/` directory.
- Keys remain server environment variables only.
- Start with SQLite for local development; use PostgreSQL for deployed multi-user work.
- Use disk for local artifacts and object storage in deployment.
- Keep API handlers thin; execution, validation, storage, and archive logic belong in separate services.
- Run generations through a background worker/task queue, never in the HTTP request thread.
