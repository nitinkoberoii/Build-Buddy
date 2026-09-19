import asyncio
import logging
import pathlib
import traceback
from typing import Callable, Awaitable, Any, Dict, Optional

from agent.graph import agent
from agent.tools import set_project_root
from api.models.generation import GenerationState

logger = logging.getLogger(__name__)

async def run_agent_generation(
    generation_id: str,
    prompt: str,
    project_dir: pathlib.Path,
    on_event: Callable[[str, str, Optional[Dict[str, Any]]], Awaitable[None]],
    on_state_change: Callable[[GenerationState, Optional[Dict[str, Any]], Optional[str]], Awaitable[None]],
    recursion_limit: int = 100,
) -> None:
    """Executes the LangGraph agent for a single generation run in an isolated project directory."""
    token = set_project_root(project_dir)
    try:
        await on_state_change(GenerationState.PLANNING, None, None)
        await on_event("planning", "Starting project planner...", None)

        inputs = {"user_prompt": prompt}
        config = {"recursion_limit": recursion_limit}

        # Run agent stream in an executor so blocking sync LLM calls don't freeze async event loop
        loop = asyncio.get_running_loop()

        def _execute_stream():
            # Ensure project root contextvar is maintained inside thread
            set_project_root(project_dir)
            events = []
            for output in agent.stream(inputs, config=config):
                events.append(output)
            return events

        outputs = await loop.run_in_executor(None, _execute_stream)

        plan_dict = None
        task_plan_dict = None

        for output in outputs:
            if "planner" in output:
                plan_obj = output["planner"].get("plan")
                if plan_obj:
                    plan_dict = plan_obj.model_dump() if hasattr(plan_obj, "model_dump") else plan_obj
                    await on_event("planning", f"Plan generated for app '{plan_dict.get('name', 'project')}'", {"plan": plan_dict})
                    await on_state_change(GenerationState.ARCHITECTING, {"plan": plan_dict}, None)

            if "architect" in output:
                task_plan_obj = output["architect"].get("task_plan")
                if task_plan_obj:
                    task_plan_dict = task_plan_obj.model_dump() if hasattr(task_plan_obj, "model_dump") else task_plan_obj
                    steps_count = len(task_plan_dict.get("implementation_steps", []))
                    await on_event("architecting", f"Architect plan ready with {steps_count} implementation tasks", {"task_plan": task_plan_dict})
                    await on_state_change(GenerationState.CODING, {"task_plan": task_plan_dict}, None)

            if "coder" in output:
                coder_state = output["coder"].get("coder_state")
                status = output["coder"].get("status")
                if coder_state:
                    step_idx = getattr(coder_state, "current_step_idx", 0)
                    await on_event("coding", f"Executed code generation step {step_idx}", {"step_index": step_idx, "status": status})

        await on_event("completed", "Project generation completed successfully", None)
        await on_state_change(GenerationState.COMPLETED, None, None)

    except asyncio.CancelledError:
        logger.warning(f"Generation run {generation_id} was cancelled.")
        await on_event("cancelled", "Generation run was cancelled", None)
        await on_state_change(GenerationState.CANCELLED, None, None)
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"Error in agent generation run {generation_id}: {error_msg}\n{traceback.format_exc()}")
        await on_event("failed", f"Generation failed: {error_msg}", {"error": error_msg})
        await on_state_change(GenerationState.FAILED, None, error_msg)
