"""SQLAlchemy database models package.

All ORM entities are exported here to ensure Alembic and SQLAlchemy metadata
discover all models when registering migrations and relationships.
"""
from api.db.base import Base
from api.db.models.user import User
from api.db.models.organization import Organization, Membership
from api.db.models.project import Project
from api.db.models.generation import Generation, GenerationEvent, ThreadMessage
from api.db.models.snapshot import ProjectSnapshot
from api.db.models.artifact import Artifact, Attachment
from api.db.models.audit import AuditLog

__all__ = [
    "Base",
    "User",
    "Organization",
    "Membership",
    "Project",
    "Generation",
    "GenerationEvent",
    "ThreadMessage",
    "ProjectSnapshot",
    "Artifact",
    "Attachment",
    "AuditLog",
]
