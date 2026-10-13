"""Repository for GenerationEvent records."""
import uuid
from typing import Optional, List, Any
from sqlalchemy import select, asc
from sqlalchemy.orm import Session

from api.db.models.generation import GenerationEvent


class EventRepository:
    """Data access repository for GenerationEvent logs."""

    @staticmethod
    def create_event(
        session: Session,
        generation_id: uuid.UUID,
        stage: str,
        message: str,
        structured_data: Optional[Any] = None,
        event_id: Optional[uuid.UUID] = None,
    ) -> GenerationEvent:
        """Appends and persists a new lifecycle event."""
        event = GenerationEvent(
            id=event_id or uuid.uuid4(),
            generation_id=generation_id,
            stage=stage,
            message=message,
            structured_data=structured_data,
        )
        session.add(event)
        session.flush()
        return event

    @staticmethod
    def get_events(session: Session, generation_id: uuid.UUID) -> List[GenerationEvent]:
        """Retrieves chronological events for a generation."""
        stmt = (
            select(GenerationEvent)
            .where(GenerationEvent.generation_id == generation_id)
            .order_by(asc(GenerationEvent.timestamp))
        )
        return list(session.execute(stmt).scalars().all())
