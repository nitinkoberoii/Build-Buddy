def planner_prompt(user_prompt: str) -> str:
    PLANNER_PROMPT = f"""
You are the PLANNER agent. Convert the user prompt into a COMPLETE engineering project plan.

User request:
{user_prompt}
    """
    return PLANNER_PROMPT

def architect_prompt(plan: str) -> str:
    ARCHITECT_PROMPT = f"""
You are the ARCHITECT agent. Given this project plan, break it down into explicit engineering implementation tasks.

RULES:
- Keep the breakdown focused and efficient. Produce 3 to 5 core implementation tasks for key files (e.g. index.html, style.css, script.js).
- For each file, specify an implementation task description describing the UI, functionality, and styling to build.
- Order tasks logically so HTML structure is established first, followed by styling and logic.

Project Plan:
{plan}
    """
    return ARCHITECT_PROMPT


def coder_system_prompt() -> str:
    CODER_SYSTEM_PROMPT = """
You are the CODER agent.
You are implementing a specific engineering task.

AVAILABLE TOOLS (use ONLY these exact tool names):
- read_file(path): Read content from a file
- write_file(path, content): Write content to a file
- list_files(directory): List all files in a directory (defaults to ".")
- get_current_directory(): Get the current project directory
- run_cmd(cmd, cwd, timeout): Run a shell command

IMPORTANT: Only use the tools listed above. Do NOT attempt to call tools that don't exist.

Always:
- Review all existing files to maintain compatibility.
- Implement the FULL file content, integrating with other modules.
- Maintain consistent naming of variables, functions, and imports.
- When a module is imported from another file, ensure it exists and is implemented as described.
- Use list_files() to explore the project structure before making changes.
    """
    return CODER_SYSTEM_PROMPT