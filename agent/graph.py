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

def planner_agent(state: dict) -> dict:
    """Converts user prompt into a structured Plan."""
    user_prompt = state["user_prompt"]
    
    # Use JSON mode instead of structured output
    llm_json = llm.bind(response_format={"type": "json_object"})
    response = llm_json.invoke(
        planner_prompt(user_prompt) + "\n\nRespond with valid JSON matching this schema: {name: string, description: string, techstack: string, features: array of strings, files: array of {path: string, purpose: string}}"
    )
    
    import json
    resp_dict = json.loads(response.content)
    resp = Plan(**resp_dict)
    
    if resp is None:
        raise ValueError("Planner did not return a valid response.")
    return {"plan": resp}

def architect_agent(state: dict) -> dict:
    """Creates TaskPlan from Plan."""
    plan: Plan = state["plan"]
    
    # Use JSON mode instead of structured output
    llm_json = llm.bind(response_format={"type": "json_object"})
    response = llm_json.invoke(
        architect_prompt(plan=plan.model_dump_json()) + "\n\nRespond with valid JSON matching this schema: {implementation_steps: array of {filepath: string, task_description: string}}"
    )
    
    import json
    resp_dict = json.loads(response.content)
    resp = TaskPlan(**resp_dict)
    
    if resp is None:
        raise ValueError("Architect did not return a valid response.")

    resp.plan = plan
    print(resp.model_dump_json())
    return {"task_plan": resp}

def coder_agent(state: dict) -> dict:
    """LangGraph tool-using coder agent."""
    coder_state: CoderState = state.get("coder_state")
    if coder_state is None:
        coder_state = CoderState(task_plan=state["task_plan"], current_step_idx=0)

    steps = coder_state.task_plan.implementation_steps
    if coder_state.current_step_idx >= len(steps):
        return {"coder_state": coder_state, "status": "DONE"}

    current_task = steps[coder_state.current_step_idx]
    
    # Check if file exists first
    try:
        existing_content = read_file.run(current_task.filepath)
    except Exception as e:
        existing_content = f"[File does not exist yet: {e}]"

    system_prompt = coder_system_prompt()
    user_prompt = (
        f"Task: {current_task.task_description}\n"
        f"File: {current_task.filepath}\n"
        f"Existing content:\n{existing_content}\n\n"
        "IMPORTANT: Use ONLY the provided tools. The available tools are:\n"
        "- read_file(path)\n"
        "- write_file(path, content)\n"
        "- list_files(directory)\n"
        "- get_current_directory()\n"
        "- run_cmd(cmd, cwd, timeout)\n\n"
        "Complete this task by writing the necessary code to the specified file."
    )

    coder_tools = [read_file, write_file, list_files, get_current_directory, run_cmd]
    react_agent = create_react_agent(llm, coder_tools)

    try:
        react_agent.invoke({"messages": [{"role": "system", "content": system_prompt},
                                         {"role": "user", "content": user_prompt}]})
    except Exception as e:
        print(f"Error in coder agent: {e}")
        # Continue to next task even if this one fails
        pass

    coder_state.current_step_idx += 1
    return {"coder_state": coder_state}


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
