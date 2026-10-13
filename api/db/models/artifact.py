"""Artifact and Attachment database models."""
import uuid
from datetime import datetime
from typing import Optional, List, Any, TYPE_CHECKING
from sqlalchemy import String, Integer, BigInteger, DateTime, ForeignKey, JSON, func, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.db.base import Base

if TYPE_CHECKING:
    from api.db.models.project import Project
    from api.db.models.generation import Generation


class Artifact(Base):
    """Generated project ZIP, snapshot bundle, or export artifact stored in object storage."""
    __tablename__ = "artifacts"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    generation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("generations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    storage_key: Mapped[str] = mapped_column(
        String(500), nullable=False, index=True
    )
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    byte_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    checksum: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="artifacts")
    generation: Mapped[Optional["Generation"]] = relationship("Generation", back_populates="artifacts")
    attachments: Mapped[List["Attachment"]] = relationship(
        "Attachment", back_populates="artifact"
    )


class Attachment(Base):
    """User-uploaded file or document attached to a generation prompt."""
    __tablename__ = "attachments"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    generation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("generations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    artifact_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("artifacts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    # Using column name "metadata" in SQL, mapped to Python attribute `file_metadata` to avoid clashing with Base.metadata
    file_metadata: Mapped[Optional[Any]] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    generation: Mapped["Generation"] = relationship("Generation", back_populates="attachments")
    artifact: Mapped[Optional["Artifact"]] = relationship("Artifact", back_populates="attachments")
