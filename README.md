# 🚀 BuildBuddy
An **Agentic AI** Software Engineer that Turns Natural Language into Real Applications.

BuildBuddy is an end-to-end agentic AI system that takes a prompt like “create a calculator app” or “build a todo application” and automatically generates a complete, runnable project — including HTML/CSS/JS files, README, tests, and all supporting structure.

Powered by **LangChain**, **LangGraph**, **FastAPI**, **React + Vite**, **Pydantic**, and **Groq LLMs**, BuildBuddy mimics how real software is built:
`planning → architecture → coding → workspace inspection`.

---

## ✨ Features

### 🧠 Planner → Architect → Coder agent pipeline
Converts user prompts into structured engineering plans, detailed file-level tasks, and actual executable code.

### ⚡ Fast Direct 1-Pass Code Generation & Self-Healing Retries
Achieves ~10–15s generation speeds using 1-pass LLM code generation. Features automated 3-attempt self-healing retry loops in `planner` and `architect` nodes to resolve JSON schema formatting issues before execution fails.

### 🌐 Modern Resizable 2-Container Workspace UI
Full-featured React + TypeScript frontend featuring a 35%/65% split resizable layout with custom drag handle, top header bar (Logo, Brand text, Project Name, ZIP download, Start New Project, User profile avatar `NK`), interactive file tree explorer (`FileTree`), live syntax-highlighted code editor (`CodeViewer`) with line numbers and copy/edit badges.

### 🚨 Failed Generation Incident Ticket & Diagnostic Recovery
If generation fails due to API limits or invalid output, an incident ticket card (`TICKET #BB-FAIL-XXXXXXXX`) renders human-understandable error descriptions, raw diagnostic logs toggle, and subdued glass action buttons (`Try Again`, `Return to Home`).

### 🔔 Bottom-Right Snackbar Toast System
Displays transient alerts for API/token notices with an animated shrinking horizontal progress countdown bar (`SnackbarToast`).

### ⌨️ Keyboard-Bound Prompt Submission
Press `Enter` in the main prompt textarea to trigger generation immediately (`Shift+Enter` for multiline input).

### ⚡ Job Cancellation
Cancel active AI generations mid-run with immediate tool execution interruption via `.cancelled` path guards.

### 🗂️ UUID-Scoped Isolation
Every generation run operates within an isolated UUID workspace (`storage/{generation_id}/project`), preventing concurrent file collisions and directory path traversal.

### 🛠️ Safe Tool-Augmented Coding
AI writes and edits files via secure I/O tools (`read_file`, `write_file`, `list_files`, `run_cmd`) with path validation and cancellation checks.

### 🔍 Agent Debugger & Tracing
Visualizes node-level state transitions (`planner → architect → coder`) and LLM trace execution via real-time SSE streams.

---

## 🏗️ Architecture Overview

BuildBuddy uses a FastAPI backend with a LangGraph state machine across three core agent nodes:

```
User Prompt (Web UI or CLI)
       ↓
 +------------------+
 |      Planner     |
 |------------------|
 | Creates project  |
 | plan: features,  |
 | files, tech stack|
 +------------------+
       ↓
 +------------------+
 |    Architect     |
 |------------------|
 | Expands each file|
 | into detailed    |
 | implementation   |
 | tasks            |
 +------------------+
       ↓
 +------------------+
 |      Coder       |
 |------------------|
 | Iteratively      |
 | writes/updates   |
 | files using      |
 | LLM + tools      |
 +------------------+
       ↓
  Project Workspace
  (/storage/{id}/project/)
```

State Flow:
- State In: `{"user_prompt": "..."}`
- Planner adds: `plan`
- Architect adds: `task_plan`
- Coder adds: `coder_state` + generated workspace files
- Status: `completed` (or `cancelled`/`failed`) → graph terminates

---

## 📦 Installation & Quickstart

### 1. Clone Repository
```bash
git clone https://github.com/nitinkoberoii/Build-Buddy.git
cd BuildBuddy
```

### 2. Install `uv` (Recommended Python Package Manager)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. Initialize Python Environment & Install Dependencies
```bash
uv sync
```

### 4. Configure API Keys
Create a `.env` file in the project root:
```env
GROQ_API_KEY=your_groq_api_key_here
```

---

## 🌐 Running the Web Application (Recommended)

### Start the FastAPI Backend Server
```bash
uv run python -m api.main
```
*Backend server will start at `http://127.0.0.1:8000`.*

### Start the React Frontend Dev Server
Open a new terminal window:
```bash
cd frontend
npm install
npm run dev
```
*Frontend application will launch at `http://localhost:5173`.*

---

## 💻 Running via CLI Mode

BuildBuddy also supports interactive command-line generation:
```bash
uv run python main.py
```
BuildBuddy will prompt for input:
```text
Enter your project prompt: create a calculator app using HTML, CSS, and JavaScript
```
Generated apps will appear under `generated_project-todo/`.

---

## 🧪 Testing & Verification

### Run Backend Unit & Integration Tests
```bash
uv run python -m pytest
```

### Verify Frontend TypeScript & Production Build
```bash
cd frontend
npm run build
```

---

## 🔌 API Endpoints

| Method | Route | Description |
| --- | --- | --- |
| `POST` | `/api/generations` | Submit prompt & start async agent generation |
| `GET` | `/api/generations` | List all historical generation runs |
| `GET` | `/api/generations/{id}` | Get status, state, plan, and error details |
| `GET` | `/api/generations/{id}/events` | Stream real-time stage progress via SSE |
| `GET` | `/api/generations/{id}/files` | Retrieve file/directory tree structure |
| `GET` | `/api/generations/{id}/files/{path}` | Read content of a specific generated file |
| `GET` | `/api/generations/{id}/download` | Download project workspace as a ZIP archive |
| `POST` | `/api/generations/{id}/cancel` | Cancel an active generation run |
| `GET` | `/api/health` | Health check endpoint |

---

## 🧪 Example Prompts

- **Calculator**: "create a simple calculator app using HTML, CSS, and JavaScript"
- **Todo Application**: "build a todo app with add/remove/update features and dark theme"
- **Weather Dashboard**: "create a weather dashboard in vanilla JS with mock forecast API integration"

---

## 📁 Generated Output Structure

Each generated project is isolated in its own workspace:
```
storage/{generation_id}/project/
│
├── index.html
├── style.css
├── script.js
└── README.md
```

---

## 🏁 Final Notes

BuildBuddy demonstrates practical agentic AI software engineering — combining structured multi-agent reasoning, safe tool execution, real-time SSE progress streaming, job cancellation, and interactive workspace UI into one cohesive system.
