"""Repository for Artifact and Attachment records."""
import uuid
from typing import Optional, List, Any
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from api.db.models.artifact import Artifact, Attachment


class ArtifactRepository:
    """Data access repository for Artifacts and Attachments."""

    @staticmethod
    def create_artifact(
        session: Session,
        project_id: uuid.UUID,
        storage_key: str,
        content_type: str,
        byte_size: int,
        generation_id: Optional[uuid.UUID] = None,
        checksum: Optional[str] = None,
        artifact_id: Optional[uuid.UUID] = None,
    ) -> Artifact:
        """Persists a new stored artifact record."""
        artifact = Artifact(
            id=artifact_id or uuid.uuid4(),
            project_id=project_id,
            generation_id=generation_id,
            storage_key=storage_key,
            content_type=content_type,
            byte_size=byte_size,
            checksum=checksum,
        )
        session.add(artifact)
        session.flush()
        return artifact

    @staticmethod
    def get_artifacts(session: Session, project_id: uuid.UUID) -> List[Artifact]:
        """Lists artifacts for a project ordered by creation time."""
        stmt = (
            select(Artifact)
            .where(Artifact.project_id == project_id)
            .order_by(desc(Artifact.created_at))
        )
        return list(session.execute(stmt).scalars().all())

    @staticmethod
    def create_attachment(
        session: Session,
        generation_id: uuid.UUID,
        original_filename: str,
        artifact_id: Optional[uuid.UUID] = None,
        file_metadata: Optional[Any] = None,
        attachment_id: Optional[uuid.UUID] = None,
    ) -> Attachment:
        """Persists a new user-uploaded attachment record."""
        attachment = Attachment(
            id=attachment_id or uuid.uuid4(),
            generation_id=generation_id,
            artifact_id=artifact_id,
            original_filename=original_filename,
            file_metadata=file_metadata,
        )
        session.add(attachment)
        session.flush()
        return attachment

    @staticmethod
    def get_attachments(session: Session, generation_id: uuid.UUID) -> List[Attachment]:
        """Lists attachments associated with a generation run."""
        stmt = select(Attachment).where(Attachment.generation_id == generation_id)
        return list(session.execute(stmt).scalars().all())
