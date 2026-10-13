"""Repository for ProjectSnapshot records."""
import uuid
from typing import Optional, List
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from api.db.models.snapshot import ProjectSnapshot


class SnapshotRepository:
    """Data access repository for ProjectSnapshots."""

    @staticmethod
    def create_snapshot(
        session: Session,
        project_id: uuid.UUID,
        version_number: int,
        manifest_location: str,
        generation_id: Optional[uuid.UUID] = None,
        creator_id: Optional[uuid.UUID] = None,
        snapshot_id: Optional[uuid.UUID] = None,
    ) -> ProjectSnapshot:
        """Persists a new version snapshot manifest for a project."""
        snapshot = ProjectSnapshot(
            id=snapshot_id or uuid.uuid4(),
            project_id=project_id,
            generation_id=generation_id,
            version_number=version_number,
            manifest_location=manifest_location,
            creator_id=creator_id,
        )
        session.add(snapshot)
        session.flush()
        return snapshot

    @staticmethod
    def get_snapshots(session: Session, project_id: uuid.UUID) -> List[ProjectSnapshot]:
        """Lists snapshots for a project ordered by version."""
        stmt = (
            select(ProjectSnapshot)
            .where(ProjectSnapshot.project_id == project_id)
            .order_by(desc(ProjectSnapshot.version_number))
        )
        return list(session.execute(stmt).scalars().all())

    @staticmethod
    def get_latest_snapshot(session: Session, project_id: uuid.UUID) -> Optional[ProjectSnapshot]:
        """Retrieves the latest version snapshot for a project."""
        stmt = (
            select(ProjectSnapshot)
            .where(ProjectSnapshot.project_id == project_id)
            .order_by(desc(ProjectSnapshot.version_number))
            .limit(1)
        )
        return session.execute(stmt).scalar_one_or_none()
