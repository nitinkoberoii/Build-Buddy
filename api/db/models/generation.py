"""Generation, GenerationEvent, and ThreadMessage database models."""
import uuid
from datetime import datetime
from typing import Optional, List, Any, TYPE_CHECKING
from sqlalchemy import String, Text, DateTime, ForeignKey, JSON, func, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.db.base import Base

if TYPE_CHECKING:
    from api.db.models.project import Project
    from api.db.models.artifact import Artifact, Attachment


class Generation(Base):
    """Generation run session for a project."""
    __tablename__ = "generations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    selected_model: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(
        String(50), nullable=False, default="queued", index=True
    )
    plan: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    task_plan: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="generations")
    events: Mapped[List["GenerationEvent"]] = relationship(
        "GenerationEvent", back_populates="generation", cascade="all, delete-orphan", order_by="GenerationEvent.timestamp"
    )
    thread_messages: Mapped[List["ThreadMessage"]] = relationship(
        "ThreadMessage", back_populates="generation", cascade="all, delete-orphan", order_by="ThreadMessage.timestamp"
    )
    attachments: Mapped[List["Attachment"]] = relationship(
        "Attachment", back_populates="generation", cascade="all, delete-orphan"
    )
    artifacts: Mapped[List["Artifact"]] = relationship(
        "Artifact", back_populates="generation"
    )


class GenerationEvent(Base):
    """Lifecycle and progress event emitted during generation."""
    __tablename__ = "generation_events"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    generation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("generations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stage: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    structured_data: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    generation: Mapped["Generation"] = relationship("Generation", back_populates="events")


class ThreadMessage(Base):
    """Iterative AI refinement chat message within a generation workspace."""
    __tablename__ = "thread_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    generation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("generations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    changed_files: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    generation: Mapped["Generation"] = relationship("Generation", back_populates="thread_messages")
