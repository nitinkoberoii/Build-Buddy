"""Repository for ThreadMessage refinement chat records."""
import uuid
from typing import Optional, List, Any
from sqlalchemy import select, asc
from sqlalchemy.orm import Session

from api.db.models.generation import ThreadMessage


class MessageRepository:
    """Data access repository for ThreadMessages."""

    @staticmethod
    def create_message(
        session: Session,
        generation_id: uuid.UUID,
        role: str,
        content: str,
        status: Optional[str] = None,
        changed_files: Optional[Any] = None,
        message_id: Optional[uuid.UUID] = None,
    ) -> ThreadMessage:
        """Appends and persists a new chat message in the generation thread."""
        message = ThreadMessage(
            id=message_id or uuid.uuid4(),
            generation_id=generation_id,
            role=role,
            content=content,
            status=status,
            changed_files=changed_files,
        )
        session.add(message)
        session.flush()
        return message

    @staticmethod
    def get_messages(session: Session, generation_id: uuid.UUID) -> List[ThreadMessage]:
        """Retrieves chronological thread messages for a generation."""
        stmt = (
            select(ThreadMessage)
            .where(ThreadMessage.generation_id == generation_id)
            .order_by(asc(ThreadMessage.timestamp))
        )
        return list(session.execute(stmt).scalars().all())

    @staticmethod
    def update_message(
        session: Session,
        message_id: uuid.UUID,
        content: Optional[str] = None,
        status: Optional[str] = None,
        changed_files: Optional[Any] = None,
    ) -> Optional[ThreadMessage]:
        """Updates content, status, or changed files of an existing thread message."""
        stmt = select(ThreadMessage).where(ThreadMessage.id == message_id)
        message = session.execute(stmt).scalar_one_or_none()
        if not message:
            return None

        if content is not None:
            message.content = content
        if status is not None:
            message.status = status
        if changed_files is not None:
            message.changed_files = changed_files

        session.flush()
        return message
