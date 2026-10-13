import asyncio
import io
import logging
import pathlib
import datetime
import uuid
import zipfile
from typing import Dict, List, Optional, Any, AsyncGenerator

from api.config import STORAGE_DIR, DEFAULT_MODEL, ALLOWED_MODELS
from api.db.base import Base
from api.db.session import SessionLocal
from api.db.models.generation import Generation as GenerationModel, GenerationEvent as GenerationEventModel
from api.db.repositories import (
    ProjectRepository,
    GenerationRepository,
    EventRepository,
    MessageRepository,
    ArtifactRepository,
    SnapshotRepository,
)
from api.models.generation import (
    GenerationResponse,
    GenerationState,
    GenerationEvent,
    FileNode,
    FileContentResponse,
    ThreadMessage,
)
from api.services.runner import run_agent_generation, run_agent_refinement

logger = logging.getLogger(__name__)


class GenerationService:
    """Service layer managing generation lifecycle, backed by SQLite/PostgreSQL repositories."""

    def __init__(self, storage_dir: pathlib.Path = STORAGE_DIR, session_factory=None):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.session_factory = session_factory or SessionLocal

        # Ensure database tables exist in the target database
        try:
            with self.session_factory() as session:
                Base.metadata.create_all(bind=session.get_bind())
        except Exception as e:
            logger.debug(f"Table verification check: {e}")

        # In-memory runtime queues and tracking for active execution and SSE streams
        self._event_queues: Dict[str, List[asyncio.Queue]] = {}
        self._active_tasks: Dict[str, asyncio.Task] = {}
        self._cancel_flags: Dict[str, bool] = {}

    def _get_run_dir(self, generation_id: str) -> pathlib.Path:
        d = self.storage_dir / generation_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _get_project_dir(self, generation_id: str) -> pathlib.Path:
        p = self._get_run_dir(generation_id) / "project"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def _orm_to_response(self, gen: GenerationModel) -> GenerationResponse:
        """Maps an ORM Generation entity and its related thread messages to a Pydantic GenerationResponse."""
        messages: List[ThreadMessage] = []
        if gen.thread_messages:
            for m in gen.thread_messages:
                messages.append(
                    ThreadMessage(
                        id=str(m.id),
                        role=m.role,
                        content=m.content,
                        timestamp=m.timestamp.isoformat() if m.timestamp else datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        status=m.status,
                        files_changed=m.changed_files if isinstance(m.changed_files, list) else None,
                    )
                )

        state_enum = GenerationState.QUEUED
        if gen.state in GenerationState._value2member_map_:
            state_enum = GenerationState(gen.state)

        created_str = gen.created_at.isoformat() if gen.created_at else datetime.datetime.now(datetime.timezone.utc).isoformat()
        updated_str = gen.updated_at.isoformat() if gen.updated_at else datetime.datetime.now(datetime.timezone.utc).isoformat()

        return GenerationResponse(
            id=str(gen.id),
            prompt=gen.prompt,
            model=gen.selected_model,
            state=state_enum,
            created_at=created_str,
            updated_at=updated_str,
            plan=gen.plan if isinstance(gen.plan, dict) else None,
            task_plan=gen.task_plan if isinstance(gen.task_plan, dict) else None,
            error=gen.error,
            messages=messages,
        )

    def _orm_to_event(self, event: GenerationEventModel) -> GenerationEvent:
        """Maps an ORM GenerationEvent entity to a Pydantic GenerationEvent schema."""
        ts_str = event.timestamp.isoformat() if event.timestamp else datetime.datetime.now(datetime.timezone.utc).isoformat()
        return GenerationEvent(
            id=str(event.id),
            generation_id=str(event.generation_id),
            stage=event.stage,
            message=event.message,
            timestamp=ts_str,
            data=event.structured_data if isinstance(event.structured_data, dict) else None,
        )

    def create_generation(
        self, prompt: str, model: Optional[str] = None, attachments: Optional[List[Dict[str, Any]]] = None
    ) -> GenerationResponse:
        """Creates database rows first, then starts async background execution."""
        selected_model = model if model and model in ALLOWED_MODELS else DEFAULT_MODEL
        gen_uuid = uuid.uuid4()
        gen_id = str(gen_uuid)

        # 1. Create database rows first
        with self.session_factory() as session:
            project = ProjectRepository.get_or_create_default_project(session)
            gen_orm = GenerationRepository.create_generation(
                session=session,
                generation_id=gen_uuid,
                project_id=project.id,
                prompt=prompt,
                selected_model=selected_model,
                state="queued",
            )
            initial_msg_id = uuid.uuid4()
            MessageRepository.create_message(
                session=session,
                generation_id=gen_uuid,
                role="user",
                content=prompt,
                message_id=initial_msg_id,
            )

            if attachments:
                for att in attachments:
                    fname = att.get("filename") or att.get("name") or "attachment"
                    ArtifactRepository.create_attachment(
                        session=session,
                        generation_id=gen_uuid,
                        original_filename=fname,
                        file_metadata=att,
                    )

            session.commit()
            response = self._orm_to_response(gen_orm)

        self._event_queues[gen_id] = []

        # 2. Record initial event (persists to generation_events table and notifies active SSE)
        self.record_event(gen_id, "queued", f"Generation request queued for model {selected_model}")

        # 3. Start async background agent execution
        project_dir = self._get_project_dir(gen_id)
        task = asyncio.create_task(
            self._execute_run(gen_id, prompt, project_dir)
        )
        self._active_tasks[gen_id] = task

        return response

    async def _execute_run(self, gen_id: str, prompt: str, project_dir: pathlib.Path) -> None:
        async def on_event(stage: str, message: str, data: Optional[Dict[str, Any]] = None):
            self.record_event(gen_id, stage, message, data)

        async def on_state_change(
            state: GenerationState,
            partial_data: Optional[Dict[str, Any]] = None,
            error: Optional[str] = None,
        ):
            plan_data = partial_data.get("plan") if partial_data else None
            task_plan_data = partial_data.get("task_plan") if partial_data else None

            # Persist state transition to database
            try:
                gen_uuid = uuid.UUID(gen_id)
                with self.session_factory() as session:
                    GenerationRepository.update_generation_state(
                        session=session,
                        generation_id=gen_uuid,
                        state=state.value,
                        plan=plan_data,
                        task_plan=task_plan_data,
                        error=error,
                    )
                    if state == GenerationState.COMPLETED:
                        existing_msgs = MessageRepository.get_messages(session, gen_uuid)
                        if not any(m.role == "assistant" for m in existing_msgs):
                            MessageRepository.create_message(
                                session=session,
                                generation_id=gen_uuid,
                                role="assistant",
                                content="Initial project workspace generated successfully.",
                                status="completed",
                            )
                    session.commit()
            except Exception as e:
                logger.error(f"Error updating generation state in DB for {gen_id}: {e}")

        try:
            await run_agent_generation(
                generation_id=gen_id,
                prompt=prompt,
                project_dir=project_dir,
                on_event=on_event,
                on_state_change=on_state_change,
                is_cancelled_check=lambda: self._cancel_flags.get(gen_id, False),
            )
        finally:
            self._active_tasks.pop(gen_id, None)

    def refine_generation(self, generation_id: str, prompt: str) -> GenerationResponse:
        """Appends a new refinement prompt to an existing generation thread and executes edits."""
        run = self.get_generation(generation_id)
        if not run:
            raise ValueError(f"Generation run '{generation_id}' not found")

        if generation_id in self._active_tasks:
            raise ValueError("A task is already actively executing for this generation thread. Please wait until it completes.")

        gen_uuid = uuid.UUID(generation_id)
        user_msg_id = uuid.uuid4()
        asst_msg_id = uuid.uuid4()

        # Refinement messages persisted to thread_messages table
        with self.session_factory() as session:
            MessageRepository.create_message(
                session=session,
                generation_id=gen_uuid,
                role="user",
                content=prompt,
                message_id=user_msg_id,
            )
            MessageRepository.create_message(
                session=session,
                generation_id=gen_uuid,
                role="assistant",
                content="Refining codebase...",
                status="refining",
                message_id=asst_msg_id,
            )
            session.commit()

        self.record_event(generation_id, "refinement_queued", f"Refinement prompt submitted: {prompt[:60]}...")

        project_dir = self._get_project_dir(generation_id)
        task = asyncio.create_task(
            self._execute_refinement(generation_id, prompt, project_dir, str(asst_msg_id))
        )
        self._active_tasks[generation_id] = task

        return self.get_generation(generation_id)  # type: ignore

    async def _execute_refinement(self, gen_id: str, prompt: str, project_dir: pathlib.Path, asst_msg_id: str) -> None:
        async def on_event(stage: str, message: str, data: Optional[Dict[str, Any]] = None):
            self.record_event(gen_id, stage, message, data)

        async def on_complete(summary: str, files_changed: List[str]):
            try:
                with self.session_factory() as session:
                    MessageRepository.update_message(
                        session=session,
                        message_id=uuid.UUID(asst_msg_id),
                        content=summary,
                        status="completed",
                        changed_files=files_changed,
                    )
                    GenerationRepository.update_generation_state(
                        session=session,
                        generation_id=uuid.UUID(gen_id),
                        state=GenerationState.COMPLETED.value,
                    )
                    session.commit()
            except Exception as e:
                logger.error(f"Error persisting refinement completion to DB: {e}")

        async def on_failure(error_msg: str):
            try:
                with self.session_factory() as session:
                    MessageRepository.update_message(
                        session=session,
                        message_id=uuid.UUID(asst_msg_id),
                        content=f"Failed to apply edits: {error_msg}",
                        status="failed",
                    )
                    session.commit()
            except Exception as e:
                logger.error(f"Error persisting refinement failure to DB: {e}")

        try:
            await run_agent_refinement(
                generation_id=gen_id,
                prompt=prompt,
                project_dir=project_dir,
                on_event=on_event,
                on_complete=on_complete,
                on_failure=on_failure,
                is_cancelled_check=lambda: self._cancel_flags.get(gen_id, False),
            )
        finally:
            self._active_tasks.pop(gen_id, None)

    def record_event(
        self, generation_id: str, stage: str, message: str, data: Optional[Dict[str, Any]] = None
    ) -> GenerationEvent:
        """Commits every event to generation_events table, then broadcasts to active SSE queues."""
        event_uuid = uuid.uuid4()
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        now_str = now_dt.isoformat()

        # Commit to generation_events table
        try:
            gen_uuid = uuid.UUID(generation_id)
            with self.session_factory() as session:
                EventRepository.create_event(
                    session=session,
                    generation_id=gen_uuid,
                    stage=stage,
                    message=message,
                    structured_data=data,
                    event_id=event_uuid,
                )
                session.commit()
        except Exception as e:
            logger.warning(f"Could not persist event {stage} to DB for {generation_id}: {e}")

        event = GenerationEvent(
            id=str(event_uuid),
            generation_id=generation_id,
            stage=stage,
            message=message,
            timestamp=now_str,
            data=data,
        )

        # Broadcast to active SSE queues
        queues = self._event_queues.get(generation_id, [])
        for q in queues:
            q.put_nowait(event)

        return event

    def get_generation(self, generation_id: str) -> Optional[GenerationResponse]:
        """Queries the database for generation details and thread messages."""
        try:
            gen_uuid = uuid.UUID(generation_id)
            with self.session_factory() as session:
                gen_orm = GenerationRepository.get_generation(session, gen_uuid)
                if gen_orm:
                    return self._orm_to_response(gen_orm)
        except (ValueError, TypeError):
            pass

        return None

    def list_generations(self) -> List[GenerationResponse]:
        """Queries the database to list all generations."""
        try:
            with self.session_factory() as session:
                gens_orm = GenerationRepository.list_generations(session)
                return [self._orm_to_response(g) for g in gens_orm]
        except Exception as e:
            logger.error(f"Error querying generations from DB: {e}")
            return []

    def get_events(self, generation_id: str) -> List[GenerationEvent]:
        """Retrieves events for a generation directly from the database."""
        try:
            gen_uuid = uuid.UUID(generation_id)
            with self.session_factory() as session:
                events_orm = EventRepository.get_events(session, gen_uuid)
                return [self._orm_to_event(e) for e in events_orm]
        except (ValueError, TypeError):
            pass

        return []

    async def subscribe_events(self, generation_id: str) -> AsyncGenerator[str, None]:
        """Yields SSE formatted string events for a generation run."""
        queue: asyncio.Queue = asyncio.Queue()
        if generation_id not in self._event_queues:
            self._event_queues[generation_id] = []
        self._event_queues[generation_id].append(queue)

        # Replay past events queried from the database
        for past_event in self.get_events(generation_id):
            yield f"event: message\ndata: {past_event.model_dump_json()}\n\n"

        try:
            while True:
                # Wait for new live events
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

    def is_cancelled(self, generation_id: str) -> bool:
        return self._cancel_flags.get(generation_id, False)

    def cancel_generation(self, generation_id: str) -> bool:
        self._cancel_flags[generation_id] = True

        # Write .cancelled marker file to signal immediate tool/graph abort
        try:
            (self._get_run_dir(generation_id) / ".cancelled").touch(exist_ok=True)
            (self._get_project_dir(generation_id) / ".cancelled").touch(exist_ok=True)
        except Exception as e:
            logger.warning(f"Could not create .cancelled marker file for {generation_id}: {e}")

        # Update database state to cancelled
        try:
            gen_uuid = uuid.UUID(generation_id)
            with self.session_factory() as session:
                GenerationRepository.update_generation_state(
                    session=session,
                    generation_id=gen_uuid,
                    state=GenerationState.CANCELLED.value,
                )
                session.commit()
        except Exception as e:
            logger.error(f"Error persisting cancelled state to DB for {generation_id}: {e}")

        self.record_event(generation_id, "cancelled", "Generation run was cancelled by user")

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
