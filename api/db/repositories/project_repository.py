"""Repository for Project and Organization entities."""
import uuid
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.db.models.organization import Organization
from api.db.models.project import Project


class ProjectRepository:
    """Data access repository for Projects and Organizations."""

    @staticmethod
    def get_or_create_default_organization(session: Session) -> Organization:
        """Finds or creates a default organization for unauthenticated / initial operations."""
        stmt = select(Organization).where(Organization.slug == "default")
        org = session.execute(stmt).scalar_one_or_none()
        if not org:
            org = Organization(
                id=uuid.uuid4(),
                name="Default Organization",
                slug="default",
            )
            session.add(org)
            session.flush()
        return org

    @classmethod
    def get_or_create_default_project(cls, session: Session) -> Project:
        """Finds or creates a default project workspace for generation runs."""
        org = cls.get_or_create_default_organization(session)
        stmt = select(Project).where(
            Project.organization_id == org.id,
            Project.name == "Default Project",
        )
        project = session.execute(stmt).scalar_one_or_none()
        if not project:
            project = Project(
                id=uuid.uuid4(),
                organization_id=org.id,
                name="Default Project",
            )
            session.add(project)
            session.flush()
        return project

    @staticmethod
    def get_or_create_project_for_organization(
        session: Session,
        organization_id: uuid.UUID,
        name: str = "Workspace Project",
        creator_id: Optional[uuid.UUID] = None,
    ) -> Project:
        """Finds or creates a project under a given tenant organization."""
        stmt = select(Project).where(
            Project.organization_id == organization_id,
            Project.name == name,
        )
        project = session.execute(stmt).scalar_one_or_none()
        if not project:
            project = Project(
                id=uuid.uuid4(),
                organization_id=organization_id,
                name=name,
                creator_id=creator_id,
            )
            session.add(project)
            session.flush()
        return project

    @staticmethod
    def get_project(session: Session, project_id: uuid.UUID) -> Optional[Project]:
        """Retrieves a project by primary key."""
        stmt = select(Project).where(Project.id == project_id)
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def create_project(
        session: Session,
        organization_id: uuid.UUID,
        name: str,
        creator_id: Optional[uuid.UUID] = None,
        project_id: Optional[uuid.UUID] = None,
    ) -> Project:
        """Creates a new project within an organization."""
        project = Project(
            id=project_id or uuid.uuid4(),
            organization_id=organization_id,
            name=name,
            creator_id=creator_id,
        )
        session.add(project)
        session.flush()
        return project
