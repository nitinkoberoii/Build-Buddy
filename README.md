# 🚀 BuildBuddy
An **Agentic AI** Software Engineer that Turns Natural Language into Real Applications.

BuildBuddy is an end-to-end agentic AI system that takes a prompt like “create a calculator app” or “build a todo application” and automatically generates a complete, runnable project — including HTML/CSS/JS files, README, tests, and all supporting structure.

Powered by **LangChain**, **LangGraph**, **Pydantic**, and **Groq LLMs**, BuilderBuddy mimics how real software is built:
`planning → architecture → coding → file generation`.

---

## ✨ Features
### 🧠 `Planner → Architect → Coder agent pipeline`
Converts user prompts into structured engineering plans, detailed file-level tasks, and actual executable code.

### 🗂️ Full project generation
Produces a complete `generated_project/` directory containing HTML, CSS, JS, README, tests, and any required assets.

### 🛠️ Safe tool-augmented coding
AI writes and edits files via secure I/O tools (read_file, write_file, list_files) with path restrictions.

### 🔍 Agent Debugger support
Visualizes node-level state transitions (planner → architect → coder) and LLM trace execution.

### ⚙️ Model-agnostic
Supports Groq's GPT-OSS models, OpenAI, Gemini, and local models via simple config changes.

---

## 🏗️ Architecture Overview
BuildBuddy uses a LangGraph state machine with three core nodes:
```
User Prompt
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
 | tasks (Jira-like)|
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
Generated Project Folder
```

State Flow:
- State In: {"user_prompt": "..."}
- Planner adds: plan
- Architect adds: task_plan
- Coder adds: coder_state + generated files
- Status: "done" → graph terminates

This mirrors a real software workflow:
`project planning → architectural breakdown → coding implementation`.

---

## 📦 Installation
- Clone Repo
```
git clone https://github.com/nitinkoberoii/Build-Buddy.git
cd BuildBuddy
```
- Install uv (recommended)
```
curl -LsSf https://astral.sh/uv/install.sh | sh
```
Note: You can also visit the site by searching `install uv` and find the guide there.

- Initialize Environment
```
uv sync
```
- Set up API Keys\
Create a .env file in the project root:
```
GROQ_API_KEY=your_key_here
```

- Run BuildBuddy
```
python main.py --prompt "create a calculator app"
```
Generated apps will appear under:
`/generated_project/`

---

## 🧪 Example Prompts
- Create a Calculator: create a simple calculator app using HTML, CSS, and JavaScript
- Generate a Todo App: build a todo app with add/remove/update features and a clean UI
- Build a Weather Dashboard: create a weather dashboard in vanilla JS with API integration

---

## 📁 Output Structure
Each generated project looks like:
```
generated_project/
│
├── index.html
├── style.css
├── script.js
├── README.md
└── test.js (optional)
```
All content is written automatically by the **Coder agent** using the implementation steps from the Architect.

---

## 🔧 Configuration
You can switch LLM providers by modifying:
```
llm = ChatGroq(model="gpt-oss-120b")
```
Supported:
- Groq GPT-OSS models (recommended / free)
- OpenAI GPT-4+/GPT-5 models
- Google Gemini models
- Local models via Ollama

---

## 🧠 Debugging with AI Agent Debugger (PyCharm)
BuildBuddy integrates perfectly with PyCharm’s Agent Debugger:
- Visualize planner → architect → coder transitions
- Inspect internal state after each step
- Track token usage and recursion depth
- Catch stuck loops and unintended logic

This massively improves reliability and explainability.

---

## 🏁 Final Notes
BuildBuddy is a real demonstration of practical agentic AI engineering — combining structured reasoning, tool use, iterative coding, and explainability into one cohesive system.

Whether you're showcasing AI engineering skills for interviews or extending it into a full product, BuildBuddy provides a solid foundation.