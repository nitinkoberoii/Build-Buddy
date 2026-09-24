# BuildBuddy architecture

## Goal

BuildBuddy turns a natural-language request into a structured starter project. The web product allows users to submit a prompt, select an LLM model, observe progress in real time via Server-Sent Events (SSE), cancel active runs, safely inspect generated files, and download the full workspace ZIP archive without exposing provider credentials.

## Current system

```text
React Client (frontend/)
  │ REST API & SSE Events
  ▼
FastAPI Service (api/main.py)
  ├── generation_service (UUID workspace scoping, state machine, event broadcasting)
  └── runner.py (async agent execution runner)
  │
  ▼
LangGraph Agent (agent/graph.py)
  ├── Planner Node → Plan schema
  ├── Architect Node → TaskPlan schema
  └── Coder Node → Tool execution loop (read_file, write_file, list_files, run_cmd)
  │
  ▼
LLM Providers (Groq, OpenAI, Ollama)
```

- `agent/graph.py` owns LangGraph execution and Groq/LLM calls.
- `agent/tools.py` supplies restricted workspace tools dynamically scoped via `ContextVar` (`set_project_root`).
- `api/` provides FastAPI REST endpoints and SSE streaming.
- `frontend/` is a React, TypeScript, Vite SPA integrated with the FastAPI backend via `api.ts` and proxy.

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
| `GET` | `/api/generations` | List all generation runs. |
| `GET` | `/api/generations/{id}` | Return state, plan, summary, and errors. |
| `GET` | `/api/generations/{id}/events` | Stream progress with SSE. |
| `GET` | `/api/generations/{id}/files` | List safe generated file tree. |
| `GET` | `/api/generations/{id}/files/{path}` | Read one validated file. |
| `GET` | `/api/generations/{id}/download` | Download an allowlisted ZIP. |
| `POST` | `/api/generations/{id}/cancel` | Request immediate cancellation of an active run. |
| `GET` | `/api/health` | Deployment health check. |

## Run states and cancellation flow

`queued → planning → architecting → coding → completed`

Terminal states: `completed`, `failed`, `cancelled`, `timed_out`.

Every state transition broadcasts a timestamped `GenerationEvent`.

### Job Cancellation Mechanism:
1. Client sends `POST /api/generations/{id}/cancel`.
2. `GenerationService.cancel_generation` sets the state to `CANCELLED`, cancels the background asyncio task, and creates `.cancelled` marker files in the run and project directories.
3. `agent/tools.py` checks for `.cancelled` on every tool invocation via `check_cancellation_active()`. If found, a `RuntimeError` is raised immediately to halt LLM tool execution.
4. `api/services/runner.py` intercepts cancellation flags/exceptions and cleanly finalizes the run state to `CANCELLED`.

## Security and storage

- Every run gets a UUID-scoped output folder under `storage/`, never the legacy shared `generated_project-todo/` directory.
- Keys remain server environment variables only.
- Start with in-memory run metadata backed by JSON files (`meta.json`, `events.json`) on disk; migrate to SQLite / PostgreSQL in Phase 4.
- Use disk for local artifacts and object storage in deployment.
- Keep API handlers thin; execution, validation, storage, and archive logic belong in `api/services/`.
- Run generations through background asyncio tasks, never blocking the HTTP request thread.

