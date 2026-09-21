import contextvars
import pathlib
import subprocess
from typing import Tuple, Optional

from langchain_core.tools import tool

_DEFAULT_PROJECT_ROOT = pathlib.Path.cwd() / "generated_project-todo"
_project_root_var: contextvars.ContextVar[pathlib.Path] = contextvars.ContextVar(
    "project_root", default=_DEFAULT_PROJECT_ROOT
)

def set_project_root(path: pathlib.Path) -> contextvars.Token:
    """Sets the workspace root path for the current context."""
    resolved_path = path.resolve()
    resolved_path.mkdir(parents=True, exist_ok=True)
    return _project_root_var.set(resolved_path)

def get_project_root() -> pathlib.Path:
    """Gets the active workspace root path for the current context."""
    root = _project_root_var.get().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root

def check_cancellation_active():
    """Checks if a cancellation signal marker exists for the active workspace."""
    root = get_project_root()
    if (root / ".cancelled").exists() or (root.parent / ".cancelled").exists():
        raise RuntimeError("Generation run cancelled by user")

def safe_path_for_project(path: str) -> pathlib.Path:
    check_cancellation_active()
    root = get_project_root()
    if not path or path == ".":
        return root
    clean_path = path.lstrip("/\\")
    p = (root / clean_path).resolve()
    if root not in p.parents and root != p.parent and root != p:
        raise ValueError(f"Attempt to access path outside project root: {path}")
    return p

@tool
def write_file(path: str, content: str) -> str:
    """Writes content to a file at the specified path within the project root."""
    check_cancellation_active()
    p = safe_path_for_project(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)
    return f"WROTE:{p}"

@tool
def read_file(path: str) -> str:
    """Reads content from a file at the specified path within the project root."""
    check_cancellation_active()
    p = safe_path_for_project(path)
    if not p.exists():
        return ""
    with open(p, "r", encoding="utf-8") as f:
        return f.read()

@tool
def get_current_directory() -> str:
    """Returns the current working directory."""
    check_cancellation_active()
    return str(get_project_root())

@tool
def list_files(directory: str = ".") -> str:
    """Lists all files and directories recursively in the specified directory within the project root. 
    Use this to explore the project structure. Directory defaults to '.' (project root)."""
    check_cancellation_active()
    root = get_project_root()
    p = safe_path_for_project(directory)
    if not p.exists():
        return f"ERROR: {p} does not exist"
    if not p.is_dir():
        return f"ERROR: {p} is not a directory"
    files = [str(f.relative_to(root)) for f in p.glob("**/*") if f.is_file()]
    return "\n".join(files) if files else "No files found."

@tool
def run_cmd(cmd: str, cwd: str = None, timeout: int = 30) -> Tuple[int, str, str]:
    """Runs a shell command in the specified directory and returns the result."""
    check_cancellation_active()
    root = get_project_root()
    cwd_dir = safe_path_for_project(cwd) if cwd else root
    res = subprocess.run(cmd, shell=True, cwd=str(cwd_dir), capture_output=True, text=True, timeout=timeout)
    check_cancellation_active()
    return res.returncode, res.stdout, res.stderr

def init_project_root() -> str:
    root = get_project_root()
    root.mkdir(parents=True, exist_ok=True)
    return str(root)
