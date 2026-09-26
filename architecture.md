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
  └── runner.py (async agent execution runner + file verification)
  │
  ▼
LangGraph Agent (agent/graph.py)
  ├── Planner Node (Self-Healing Retry Loop, 3 attempts) → Plan schema
  ├── Architect Node (Self-Healing Retry Loop, 3 attempts) → TaskPlan schema (3-5 core tasks)
  └── Coder Node (Direct 1-Pass Code Generation) → write_file.invoke({...})
  │
  ▼
LLM Providers (Groq / OpenAI / Ollama)
```

- `agent/graph.py` owns LangGraph execution, Groq LLM invocations, self-healing retries, and fast 1-pass file generation.
- `agent/tools.py` supplies restricted workspace tools dynamically scoped via `ContextVar` (`set_project_root`).
- `api/` provides FastAPI REST endpoints, SSE streaming, and output validation in `runner.py`.
- `frontend/` is a React, TypeScript, Vite SPA integrated with the FastAPI backend via `api.ts` and Vite proxy.

## Agent Node Architecture & Optimizations

### 1. Self-Healing Planner & Architect Nodes
- **Retry Mechanism**: Both `planner_agent` and `architect_agent` execute inside a 3-attempt retry loop (`for attempt in range(3)`).
- **Auto-Correction**: If the LLM returns unstructured output or malformed JSON, a recovery prompt detailing the exact Pydantic schema validation error is injected into the next retry iteration.
- **Task Conciseness**: `architect_prompt` limits file tasks to 3–5 core implementation files for maximum output speed (~10–15s).

### 2. Fast Direct 1-Pass Code Generation (`coder_agent`)
- **Direct Output Generation**: Replaces multi-turn ReAct reasoning loops per file with a single direct LLM call per task file.
- **Explicit Tool Execution**: Calls `write_file.invoke({"path": file_path, "content": file_content})` using structured dictionaries, resolving LangChain `BaseTool.run()` argument mismatch errors.
- **Fallback Extraction**: If the LLM wraps code inside standard message text instead of tool calls, `coder_agent` automatically parses block text and writes the payload to disk.

### 4. Incremental AI Refinement Agent (`refine_project_agent`)
- **Targeted Codebase Updates**: Executed via `POST /api/generations/{id}/refine`. Reads existing project workspace files and applies precise edits to existing files or creates new files without resetting the workspace.
- **Thread Message Log**: Stores thread messages (`ThreadMessage`) in run metadata (`meta.json`) and streams progress events (`refinement_queued`, `refining`, `refinement_completed`) over SSE.

## Frontend Component Architecture & UX System

```text
App.tsx (Root State, URL Hash & Path Routing #/project/:id, Persistence)
 ├── Landing View (Navbar, Hero Prompt Input, Model Selector, Review Section, Footer)
 ├── LoadingScreen.tsx (SSE Live Terminal Logs, Cancellation Action, Incident Ticket Card)
 ├── ProjectWorkspace.tsx (Top Toolbar, 35%/65% Resizable Containers, File Tree, Live Code Viewer, AI Edit Prompt Box)
 └── SnackbarToast.tsx (Bottom-Right Toast, Animated Horizontal Progress Line)
```

### 1. Resizable Split Workspace Container & AI Refinement Panel (`ProjectWorkspace.tsx`)
- **Header Toolbar**: Displays BuildBuddy logo, brand name, Project Name badge, Download .ZIP CTA, "＋ Start New Project" button, and user profile avatar (`NK`).
- **Resizable Layout**: Split into two vertically resizable container cards (default 35% left container for `FileTree` & AI Refinement Prompt Box, 65% right container for `CodeViewer`). Resized dynamically via mouse drag handle (`resizer-gutter`).
- **AI Refinement Panel**: Positioned directly beneath the file tree explorer in the left panel. Contains a scrollable thread message log, action toolbar buttons (`📋 Copy`, `🔄 Regenerate`, `✏️ Edit`), and an edit prompt textarea.
- **Code Editor (`CodeViewer.tsx`)**: Renders file header badges (`Filename`, `Language`), Copy code button, Edit mode toggle, line numbers gutter, custom dark scrollbar, and editable code textarea.

### 2. URL Routing & Workspace Reload Persistence
- **Route Format**: `#/project/<generation_id>` or `/project/<generation_id>`.
- **Persistence**: Page reloads (`F5`) or direct links parse the project ID, fetch workspace data via `getGeneration(id)`, and automatically display the active workspace.

### 3. Incident Ticket System (`LoadingScreen.tsx`)
- **Trigger**: Activated when run status becomes `FAILED` or an exception is caught.
- **UI Card**: Renders `TICKET #BB-FAIL-XXXXXXXX`, human-readable cause analysis (e.g. rate limit, schema parsing, 0 files created), expandable raw diagnostic logs, and subdued glass action buttons (`Try Again`, `Return to Home`).

### 4. Snackbar Toast Notifications (`SnackbarToast.tsx`)
- **Transient Alerts**: Positioned at bottom-right (`fixed bottom-6 right-6`). Includes icon, title, message, close button, and an animated shrinking horizontal line indicator (`durationMs`).

## MVP API

| Method | Route | Purpose |
| --- | --- | --- |
| `POST` | `/api/generations` | Start a validated generation; return run ID. |
| `POST` | `/api/generations/{id}/refine` | Submit edit prompt to refine existing workspace files. |
| `GET` | `/api/generations` | List all generation runs. |
| `GET` | `/api/generations/{id}` | Return state, plan, messages, summary, and errors. |
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

