import asyncio
import io
import json
import logging
import pathlib
import datetime
import uuid
import zipfile
from typing import Dict, List, Optional, Any, AsyncGenerator

from api.config import STORAGE_DIR, DEFAULT_MODEL, ALLOWED_MODELS
from api.models.generation import (
    GenerationResponse,
    GenerationState,
    GenerationEvent,
    FileNode,
    FileContentResponse,
)
from api.services.runner import run_agent_generation

logger = logging.getLogger(__name__)

class GenerationService:
    def __init__(self, storage_dir: pathlib.Path = STORAGE_DIR):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._runs: Dict[str, GenerationResponse] = {}
        self._events: Dict[str, List[GenerationEvent]] = {}
        self._event_queues: Dict[str, List[asyncio.Queue]] = {}
        self._active_tasks: Dict[str, asyncio.Task] = {}
        self._load_existing_runs()

    def _load_existing_runs(self) -> None:
        """Loads saved generation metadata from disk on startup."""
        for item in self.storage_dir.iterdir():
            if item.is_dir():
                meta_file = item / "meta.json"
                if meta_file.exists():
                    try:
                        with open(meta_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        resp = GenerationResponse(**data)
                        self._runs[resp.id] = resp
                    except Exception as e:
                        logger.error(f"Failed to load run metadata for {item.name}: {e}")

    def _get_run_dir(self, generation_id: str) -> pathlib.Path:
        d = self.storage_dir / generation_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _get_project_dir(self, generation_id: str) -> pathlib.Path:
        p = self._get_run_dir(generation_id) / "project"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def _save_run_meta(self, run: GenerationResponse) -> None:
        run_dir = self._get_run_dir(run.id)
        meta_file = run_dir / "meta.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(run.model_dump(), f, indent=2)

    def _save_events(self, generation_id: str) -> None:
        run_dir = self._get_run_dir(generation_id)
        events_file = run_dir / "events.json"
        events_list = [e.model_dump() for e in self._events.get(generation_id, [])]
        with open(events_file, "w", encoding="utf-8") as f:
            json.dump(events_list, f, indent=2)

    def create_generation(
        self, prompt: str, model: Optional[str] = None, attachments: Optional[List[Dict[str, Any]]] = None
    ) -> GenerationResponse:
        """Creates a new generation run record and starts async execution."""
        selected_model = model if model and model in ALLOWED_MODELS else DEFAULT_MODEL
        gen_id = str(uuid.uuid4())
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        run = GenerationResponse(
            id=gen_id,
            prompt=prompt,
            model=selected_model,
            state=GenerationState.QUEUED,
            created_at=now,
            updated_at=now,
        )

        self._runs[gen_id] = run
        self._events[gen_id] = []
        self._event_queues[gen_id] = []
        self._save_run_meta(run)

        # Record initial event
        self.record_event(gen_id, "queued", f"Generation request queued for model {selected_model}")

        # Start async background agent execution
        project_dir = self._get_project_dir(gen_id)
        task = asyncio.create_task(
            self._execute_run(gen_id, prompt, project_dir)
        )
        self._active_tasks[gen_id] = task

        return run

    async def _execute_run(self, gen_id: str, prompt: str, project_dir: pathlib.Path) -> None:
        async def on_event(stage: str, message: str, data: Optional[Dict[str, Any]] = None):
            self.record_event(gen_id, stage, message, data)

        async def on_state_change(
            state: GenerationState,
            partial_data: Optional[Dict[str, Any]] = None,
            error: Optional[str] = None,
        ):
            run = self._runs.get(gen_id)
            if not run:
                return
            run.state = state
            run.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
            if partial_data:
                if "plan" in partial_data:
                    run.plan = partial_data["plan"]
                if "task_plan" in partial_data:
                    run.task_plan = partial_data["task_plan"]
            if error:
                run.error = error
            self._save_run_meta(run)

        try:
            await run_agent_generation(
                generation_id=gen_id,
                prompt=prompt,
                project_dir=project_dir,
                on_event=on_event,
                on_state_change=on_state_change,
            )
        finally:
            self._active_tasks.pop(gen_id, None)

    def record_event(
        self, generation_id: str, stage: str, message: str, data: Optional[Dict[str, Any]] = None
    ) -> GenerationEvent:
        """Records a timestamped event and broadcasts it to active SSE subscribers."""
        event_id = str(uuid.uuid4())
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        event = GenerationEvent(
            id=event_id,
            generation_id=generation_id,
            stage=stage,
            message=message,
            timestamp=now,
            data=data,
        )

        if generation_id not in self._events:
            self._events[generation_id] = []
        self._events[generation_id].append(event)
        self._save_events(generation_id)

        # Broadcast to active SSE queues
        queues = self._event_queues.get(generation_id, [])
        for q in queues:
            q.put_nowait(event)

        return event

    def get_generation(self, generation_id: str) -> Optional[GenerationResponse]:
        return self._runs.get(generation_id)

    def list_generations(self) -> List[GenerationResponse]:
        return list(self._runs.values())

    def get_events(self, generation_id: str) -> List[GenerationEvent]:
        return self._events.get(generation_id, [])

    async def subscribe_events(self, generation_id: str) -> AsyncGenerator[str, None]:
        """Yields SSE formatted string events for a generation run."""
        queue: asyncio.Queue = asyncio.Queue()
        if generation_id not in self._event_queues:
            self._event_queues[generation_id] = []
        self._event_queues[generation_id].append(queue)

        # Replay past events first
        for past_event in self.get_events(generation_id):
            yield f"event: message\ndata: {past_event.model_dump_json()}\n\n"

        try:
            while True:
                # Wait for new events
                event: GenerationEvent = await queue.get()
                yield f"event: message\ndata: {event.model_dump_json()}\n\n"
                run = self.get_generation(generation_id)
                if run and run.state in (
                    GenerationState.COMPLETED,
                    GenerationState.FAILED,
                    GenerationState.CANCELLED,
                ):
                    # End SSE stream when terminal state is reached
                    break
        finally:
            if generation_id in self._event_queues:
                self._event_queues[generation_id].remove(queue)

    def cancel_generation(self, generation_id: str) -> bool:
        task = self._active_tasks.get(generation_id)
        if task and not task.done():
            task.cancel()
            return True
        return False

    def get_file_tree(self, generation_id: str) -> List[FileNode]:
        """Returns structured file/directory tree for the generation project workspace."""
        project_dir = self._get_project_dir(generation_id)
        if not project_dir.exists():
            return []

        def build_nodes(dir_path: pathlib.Path) -> List[FileNode]:
            nodes = []
            for item in sorted(dir_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
                rel_path = str(item.relative_to(project_dir))
                if item.is_dir():
                    children = build_nodes(item)
                    nodes.append(
                        FileNode(
                            name=item.name,
                            path=rel_path,
                            type="directory",
                            children=children,
                        )
                    )
                else:
                    nodes.append(
                        FileNode(
                            name=item.name,
                            path=rel_path,
                            type="file",
                            size=item.stat().st_size,
                        )
                    )
            return nodes

        return build_nodes(project_dir)

    def read_file_content(self, generation_id: str, relative_path: str) -> FileContentResponse:
        """Reads file content safely from the project directory."""
        project_dir = self._get_project_dir(generation_id).resolve()
        clean_rel = relative_path.lstrip("/\\")
        target_file = (project_dir / clean_rel).resolve()

        if project_dir not in target_file.parents and project_dir != target_file:
            raise ValueError("Access denied: path outside project directory")

        if not target_file.exists() or not target_file.is_file():
            raise FileNotFoundError(f"File not found: {relative_path}")

        with open(target_file, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        return FileContentResponse(
            path=clean_rel,
            content=content,
            size=target_file.stat().st_size,
        )

    def create_project_zip(self, generation_id: str) -> bytes:
        """Creates an in-memory ZIP archive of all files in the project workspace."""
        project_dir = self._get_project_dir(generation_id)
        buffer = io.BytesIO()

        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in project_dir.glob("**/*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(project_dir)
                    zip_file.write(file_path, arcname=str(arcname))

        buffer.seek(0)
        return buffer.getvalue()

# Global singleton service instance
generation_service = GenerationService()
