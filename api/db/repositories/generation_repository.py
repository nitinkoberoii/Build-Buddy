"""Repository for Generation runs."""
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Any
from sqlalchemy import select, desc
from sqlalchemy.orm import Session, selectinload

from api.db.models.generation import Generation


class GenerationRepository:
    """Data access repository for Generation records."""

    @staticmethod
    def create_generation(
        session: Session,
        generation_id: uuid.UUID,
        project_id: uuid.UUID,
        prompt: str,
        selected_model: str,
        state: str = "queued",
        plan: Optional[Any] = None,
        task_plan: Optional[Any] = None,
        error: Optional[str] = None,
    ) -> Generation:
        """Creates and persists a new generation record."""
        generation = Generation(
            id=generation_id,
            project_id=project_id,
            prompt=prompt,
            selected_model=selected_model,
            state=state,
            plan=plan,
            task_plan=task_plan,
            error=error,
        )
        session.add(generation)
        session.flush()
        return generation

    @staticmethod
    def get_generation(session: Session, generation_id: uuid.UUID) -> Optional[Generation]:
        """Retrieves a generation by primary key with thread messages eager loaded."""
        stmt = (
            select(Generation)
            .where(Generation.id == generation_id)
            .options(
                selectinload(Generation.thread_messages),
                selectinload(Generation.events),
            )
        )
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def list_generations(
        session: Session,
        project_id: Optional[uuid.UUID] = None,
        limit: int = 100,
    ) -> List[Generation]:
        """Lists generations ordered from most recent to oldest."""
        stmt = (
            select(Generation)
            .options(selectinload(Generation.thread_messages))
            .order_by(desc(Generation.created_at))
            .limit(limit)
        )
        if project_id:
            stmt = stmt.where(Generation.project_id == project_id)
        return list(session.execute(stmt).scalars().all())

    @staticmethod
    def get_generation_in_organization(
        session: Session,
        generation_id: uuid.UUID,
        organization_id: uuid.UUID,
    ) -> Optional[Generation]:
        """Retrieves a generation ensuring it belongs to the authenticated user's organization."""
        from api.db.models.project import Project
        stmt = (
            select(Generation)
            .join(Project, Generation.project_id == Project.id)
            .where(
                Generation.id == generation_id,
                Project.organization_id == organization_id,
            )
            .options(
                selectinload(Generation.thread_messages),
                selectinload(Generation.events),
            )
        )
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def list_generations_for_organization(
        session: Session,
        organization_id: uuid.UUID,
        limit: int = 100,
    ) -> List[Generation]:
        """Lists generations belonging to projects in the authenticated organization."""
        from api.db.models.project import Project
        stmt = (
            select(Generation)
            .join(Project, Generation.project_id == Project.id)
            .where(Project.organization_id == organization_id)
            .options(selectinload(Generation.thread_messages))
            .order_by(desc(Generation.created_at))
            .limit(limit)
        )
        return list(session.execute(stmt).scalars().all())

    @staticmethod
    def update_generation_state(
        session: Session,
        generation_id: uuid.UUID,
        state: str,
        plan: Optional[Any] = None,
        task_plan: Optional[Any] = None,
        error: Optional[str] = None,
    ) -> Optional[Generation]:
        """Updates lifecycle state and output artifacts of a generation."""
        stmt = select(Generation).where(Generation.id == generation_id)
        generation = session.execute(stmt).scalar_one_or_none()
        if not generation:
            return None

        generation.state = state
        if plan is not None:
            generation.plan = plan
        if task_plan is not None:
            generation.task_plan = task_plan
        if error is not None:
            generation.error = error
        generation.updated_at = datetime.now(timezone.utc)
        session.flush()
        return generation
