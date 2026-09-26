from dotenv import load_dotenv
from langchain_core.globals import set_verbose, set_debug
from langchain_groq import ChatGroq
from langgraph.constants import END
from langgraph.graph import StateGraph
from langgraph.prebuilt import create_react_agent

from agent.prompts import *
from agent.states import *
from agent.tools import *

_ = load_dotenv()

set_debug(True)
set_verbose(True)

llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)

def _sanitize_plan_dict(resp_dict: dict, user_prompt: str) -> dict:
    if not isinstance(resp_dict, dict):
        resp_dict = {}

    name = str(resp_dict.get("name") or "Generated Application").strip()
    description = str(resp_dict.get("description") or user_prompt).strip()
    techstack = str(resp_dict.get("techstack") or "HTML, CSS, JavaScript").strip()

    features = resp_dict.get("features", [])
    if not isinstance(features, list):
        features = ["Interactive UI", "Responsive Design"]
    clean_features = [str(f).strip() for f in features if str(f).strip()]

    files = resp_dict.get("files", [])
    if not isinstance(files, list):
        files = []
    clean_files = []
    for f in files:
        if isinstance(f, dict):
            p = str(f.get("path") or "index.html").strip()
            purp = str(f.get("purpose") or "Main file").strip()
            clean_files.append({"path": p, "purpose": purp})
        elif isinstance(f, str) and f.strip():
            clean_files.append({"path": f.strip(), "purpose": "Application file"})

    if not clean_files:
        clean_files = [
            {"path": "index.html", "purpose": "Main markup structure"},
            {"path": "style.css", "purpose": "Styling and layout"},
            {"path": "script.js", "purpose": "Interactive logic"},
        ]

    return {
        "name": name,
        "description": description,
        "techstack": techstack,
        "features": clean_features or ["Core Application Logic"],
        "files": clean_files,
    }


def _sanitize_task_plan_dict(resp_dict: dict) -> dict:
    steps = resp_dict.get("implementation_steps", [])
    if not isinstance(steps, list):
        steps = []

    clean_steps = []
    for step in steps:
        if isinstance(step, str):
            clean_str = step.strip()
            if not clean_str:
                continue
            parts = clean_str.split(":", 1)
            if len(parts) == 2 and ("." in parts[0] or "/" in parts[0]):
                clean_steps.append({
                    "filepath": parts[0].strip(),
                    "task_description": parts[1].strip() or clean_str,
                })
            else:
                clean_steps.append({
                    "filepath": "index.html",
                    "task_description": clean_str,
                })
        elif isinstance(step, dict):
            fp = str(step.get("filepath", "index.html") or "index.html").strip()
            desc = str(
                step.get("task_description", "")
                or step.get("description", "")
                or f"Implement {fp}"
            ).strip()
            if not fp:
                fp = "index.html"
            if not desc:
                desc = f"Implement {fp}"
            clean_steps.append({"filepath": fp, "task_description": desc})

    if not clean_steps:
        clean_steps = [
            {"filepath": "index.html", "task_description": "Create base index.html file with app layout."},
            {"filepath": "style.css", "task_description": "Create style.css with modern dark UI styling."},
            {"filepath": "script.js", "task_description": "Implement core application logic in script.js."},
        ]

    resp_dict["implementation_steps"] = clean_steps
    return resp_dict


def planner_agent(state: dict) -> dict:
    """Converts user prompt into a structured Plan with self-healing retries."""
    check_cancellation_active()
    user_prompt = state["user_prompt"]

    max_retries = 3
    last_error = None

    for attempt in range(1, max_retries + 1):
        check_cancellation_active()
        try:
            llm_json = llm.bind(response_format={"type": "json_object"})
            prompt_text = (
                planner_prompt(user_prompt)
                + "\n\nRespond with valid JSON matching this schema: {name: string, description: string, techstack: string, features: array of strings, files: array of {path: string, purpose: string}}"
            )
            if last_error:
                prompt_text += f"\n\nCRITICAL FIX: Your previous response failed schema validation with: {last_error}. Respond strictly with a valid JSON object."

            response = llm_json.invoke(prompt_text)
            import json

            resp_dict = json.loads(response.content)
            sanitized_dict = _sanitize_plan_dict(resp_dict, user_prompt)
            resp = Plan(**sanitized_dict)
            if resp:
                return {"plan": resp}
        except Exception as e:
            last_error = str(e)
            print(f"Planner attempt {attempt}/{max_retries} failed: {e}")
            if attempt == max_retries:
                raise ValueError(f"Planner agent failed after {max_retries} attempts: {e}")


def architect_agent(state: dict) -> dict:
    """Creates TaskPlan from Plan with self-healing retries."""
    check_cancellation_active()
    plan: Plan = state["plan"]

    max_retries = 3
    last_error = None

    for attempt in range(1, max_retries + 1):
        check_cancellation_active()
        try:
            llm_json = llm.bind(response_format={"type": "json_object"})
            prompt_text = (
                architect_prompt(plan=plan.model_dump_json())
                + "\n\nRespond with valid JSON matching this schema: {implementation_steps: array of {filepath: string, task_description: string}}"
            )
            if last_error:
                prompt_text += f"\n\nCRITICAL FIX: Your previous response failed with: {last_error}. Ensure implementation_steps is an array of objects with 'filepath' and 'task_description'."

            response = llm_json.invoke(prompt_text)
            import json

            resp_dict = json.loads(response.content)
            sanitized_dict = _sanitize_task_plan_dict(resp_dict)
            resp = TaskPlan(**sanitized_dict)
            if resp:
                resp.plan = plan
                print(resp.model_dump_json())
                return {"task_plan": resp}
        except Exception as e:
            last_error = str(e)
            print(f"Architect attempt {attempt}/{max_retries} failed: {e}")
            if attempt == max_retries:
                raise ValueError(f"Architect agent failed after {max_retries} attempts: {e}")



def coder_agent(state: dict) -> dict:
    """Fast & robust direct code generation agent."""
    check_cancellation_active()
    coder_state: CoderState = state.get("coder_state")
    if coder_state is None:
        coder_state = CoderState(task_plan=state["task_plan"], current_step_idx=0)

    steps = coder_state.task_plan.implementation_steps
    if coder_state.current_step_idx >= len(steps):
        return {"coder_state": coder_state, "status": "DONE"}

    current_task = steps[coder_state.current_step_idx]

    try:
        existing_content = read_file.invoke({"path": current_task.filepath})
    except Exception:
        existing_content = ""

    prompt = (
        f"You are BuildBuddy, an expert senior developer.\n"
        f"Task: {current_task.task_description}\n"
        f"File: {current_task.filepath}\n"
        f"Existing content:\n{existing_content}\n\n"
        "Generate the COMPLETE, production-ready code for this file. "
        "Return ONLY the raw code content for the file."
    )

    clean_content = ""
    try:
        res = llm.invoke(prompt)
        if hasattr(res, "tool_calls") and res.tool_calls:
            args = res.tool_calls[0].get("args", {})
            if isinstance(args, dict):
                clean_content = args.get("arguments") or args.get("code") or str(args)
            elif isinstance(args, str):
                clean_content = args
        if not clean_content and hasattr(res, "content"):
            clean_content = str(res.content)
    except Exception as exc:
        err_str = str(exc)
        if "cancelled" in err_str.lower() or isinstance(exc, RuntimeError):
            raise exc

        # Extract code from Groq 400 failed_generation payload if present
        if "failed_generation" in err_str:
            import json, re
            match = re.search(r"'failed_generation':\s*'({.*?})'", err_str, re.DOTALL)
            if match:
                raw_payload = match.group(1)
                try:
                    fg_json = json.loads(raw_payload.replace("\\'", "'"))
                    clean_content = fg_json.get("arguments") or fg_json.get("code") or ""
                except Exception:
                    clean_content = raw_payload

        if not clean_content:
            print(f"Error in coder agent step for {current_task.filepath}: {exc}")

    if clean_content:
        clean_content = clean_content.strip()
        if clean_content.startswith("```"):
            lines = clean_content.split("\n")
            if len(lines) >= 2:
                end_idx = -1 if lines[-1].strip().startswith("```") else len(lines)
                clean_content = "\n".join(lines[1:end_idx])
        write_file.invoke({"path": current_task.filepath, "content": clean_content})


    coder_state.current_step_idx += 1
    return {"coder_state": coder_state}


def refine_project_agent(user_prompt: str, project_dir) -> dict:
    """Modifies targeted project file(s) or creates a single new file based on user edit request."""
    set_project_root(project_dir)
    check_cancellation_active()

    all_files = []
    for item in project_dir.glob("**/*"):
        if item.is_file() and not item.name.startswith("."):
            rel_path = str(item.relative_to(project_dir))
            try:
                with open(item, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                all_files.append({"path": rel_path, "content": content})
            except Exception:
                pass

    files_summary = ""
    for f in all_files:
        files_summary += f"\n--- FILE: {f['path']} ---\n{f['content']}\n"

    system_prompt = (
        "You are BuildBuddy, an expert senior web developer performing a targeted incremental update to an existing codebase.\n"
        "RULES:\n"
        "1. DO NOT rewrite the entire codebase unnecessarily. Modify ONLY the files relevant to the user request, or create a new file if explicitly requested.\n"
        "2. Provide COMPLETE production-ready file contents for any modified or new files (no placeholders, no '// ... existing code').\n"
        "3. Keep all existing features and styling intact unless the user requested changing them.\n\n"
        "Existing Codebase Files:\n"
        f"{files_summary}\n\n"
        "User Edit Request:\n"
        f"{user_prompt}\n\n"
        "Respond strictly with valid JSON matching this schema:\n"
        "{\n"
        '  "summary": "Clear, short bullet summary of changes made",\n'
        '  "changes": [\n'
        '    {\n'
        '      "filepath": "relative/path/to/file.ext",\n'
        '      "action": "update" or "create",\n'
        '      "content": "COMPLETE full content of the file"\n'
        '    }\n'
        '  ]\n'
        "}"
    )

    check_cancellation_active()
    llm_json = llm.bind(response_format={"type": "json_object"})

    max_retries = 3
    last_error = None
    resp_dict = None

    for attempt in range(1, max_retries + 1):
        check_cancellation_active()
        try:
            p_text = system_prompt
            if last_error:
                p_text += f"\n\nCRITICAL FIX: Your previous JSON response failed with: {last_error}. Ensure valid JSON schema."

            response = llm_json.invoke(p_text)
            import json

            resp_dict = json.loads(response.content)
            if isinstance(resp_dict, dict) and "changes" in resp_dict:
                break
        except Exception as e:
            last_error = str(e)
            print(f"Refinement attempt {attempt}/{max_retries} failed: {e}")
            if attempt == max_retries:
                raise ValueError(f"Refinement agent failed after {max_retries} attempts: {e}")

    if not resp_dict or not isinstance(resp_dict.get("changes"), list):
        raise ValueError("Refinement agent failed to produce valid file changes list.")

    modified_paths = []
    summary = str(resp_dict.get("summary") or "Applied requested project edits.").strip()

    for change in resp_dict["changes"]:
        check_cancellation_active()
        if not isinstance(change, dict):
            continue
        filepath = str(change.get("filepath", "")).strip().lstrip("/\\")
        content = str(change.get("content", "")).strip()
        if not filepath or not content:
            continue

        if content.startswith("```"):
            lines = content.split("\n")
            if len(lines) >= 2:
                end_idx = -1 if lines[-1].strip().startswith("```") else len(lines)
                content = "\n".join(lines[1:end_idx]).strip()

        write_file.invoke({"path": filepath, "content": content})
        modified_paths.append(filepath)

    return {
        "summary": summary,
        "files_changed": modified_paths,
    }


graph = StateGraph(dict)

graph.add_node("planner", planner_agent)
graph.add_node("architect", architect_agent)
graph.add_node("coder", coder_agent)

graph.add_edge("planner", "architect")
graph.add_edge("architect", "coder")
graph.add_conditional_edges(
    "coder",
    lambda s: "END" if s.get("status") == "DONE" else "coder",
    {"END": END, "coder": "coder"}
)

graph.set_entry_point("planner")
agent = graph.compile()

if __name__ == "__main__":
    result = agent.invoke({"user_prompt": "Build a colourful modern todo app in html css and js"},
                          {"recursion_limit": 100})
    print("Final State:", result)

