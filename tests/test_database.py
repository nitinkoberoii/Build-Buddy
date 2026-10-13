"""Tests for database models, tenancy hierarchy, constraints, and migrations."""
import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from api.db.base import Base
from api.db.models import (
    User,
    Organization,
    Membership,
    Project,
    Generation,
    GenerationEvent,
    ThreadMessage,
    ProjectSnapshot,
    Artifact,
    Attachment,
    AuditLog,
)


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database session with foreign keys enabled."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    # Enable SQLite foreign key constraints
    from sqlalchemy import event
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_core_tenancy_hierarchy_and_relationships(db_session):
    """Verify users -> memberships -> organizations -> projects -> generations."""
    # 1. Create User
    user = User(
        email="founder@buildbuddy.dev",
        status="active",
        password_hash="argon2id_mock_hash",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    assert user.id is not None

    # 2. Create Organization
    org = Organization(
        name="BuildBuddy Team",
        slug="buildbuddy-team",
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    assert org.id is not None

    # 3. Create Membership
    membership = Membership(
        user_id=user.id,
        organization_id=org.id,
        role="owner",
    )
    db_session.add(membership)
    db_session.commit()
    db_session.refresh(membership)
    assert membership.user.email == "founder@buildbuddy.dev"
    assert membership.organization.name == "BuildBuddy Team"

    # 4. Create Project
    project = Project(
        organization_id=org.id,
        name="Portfolio Builder",
        creator_id=user.id,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    assert project.organization.slug == "buildbuddy-team"
    assert project.creator.email == "founder@buildbuddy.dev"

    # 5. Create Generation
    gen = Generation(
        project_id=project.id,
        prompt="Build a clean developer portfolio with dark theme",
        selected_model="openai/gpt-oss-20b",
        state="planning",
        plan={"overview": "Portfolio with grid gallery"},
    )
    db_session.add(gen)
    db_session.commit()
    db_session.refresh(gen)
    assert gen.project.name == "Portfolio Builder"
    assert gen.state == "planning"

    # 6. Create GenerationEvent & ThreadMessage
    event = GenerationEvent(
        generation_id=gen.id,
        stage="planning",
        message="Generated architecture plan",
        structured_data={"files": ["index.html", "style.css"]},
    )
    thread_msg = ThreadMessage(
        generation_id=gen.id,
        role="user",
        content="Make the navigation bar sticky",
    )
    db_session.add_all([event, thread_msg])
    db_session.commit()

    db_session.refresh(gen)
    assert len(gen.events) == 1
    assert gen.events[0].stage == "planning"
    assert len(gen.thread_messages) == 1
    assert gen.thread_messages[0].content == "Make the navigation bar sticky"


def test_unique_constraints(db_session):
    """Verify unique constraints on user email, org slug, and membership pair."""
    # Duplicate user email
    user1 = User(email="test@example.com")
    db_session.add(user1)
    db_session.commit()

    user2 = User(email="test@example.com")
    db_session.add(user2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Duplicate org slug
    org1 = Organization(name="Org One", slug="shared-slug")
    db_session.add(org1)
    db_session.commit()

    org2 = Organization(name="Org Two", slug="shared-slug")
    db_session.add(org2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Duplicate membership pair
    u = User(email="member@example.com")
    o = Organization(name="Acme", slug="acme")
    db_session.add_all([u, o])
    db_session.commit()

    m1 = Membership(user_id=u.id, organization_id=o.id, role="admin")
    db_session.add(m1)
    db_session.commit()

    m2 = Membership(user_id=u.id, organization_id=o.id, role="viewer")
    db_session.add(m2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_artifacts_snapshots_and_audit_logs(db_session):
    """Verify snapshot, artifact, attachment, and audit log models."""
    org = Organization(name="Lab", slug="lab")
    db_session.add(org)
    db_session.commit()

    proj = Project(organization_id=org.id, name="Snapshot Lab")
    db_session.add(proj)
    db_session.commit()

    gen = Generation(
        project_id=proj.id,
        prompt="Test snapshots",
        selected_model="openai/gpt-oss-20b",
        state="completed",
    )
    db_session.add(gen)
    db_session.commit()

    # Artifact
    artifact = Artifact(
        project_id=proj.id,
        generation_id=gen.id,
        storage_key="s3://artifacts/proj-123/bundle.zip",
        content_type="application/zip",
        byte_size=1024,
        checksum="sha256-mock-checksum",
    )
    db_session.add(artifact)
    db_session.commit()

    # Attachment
    attachment = Attachment(
        generation_id=gen.id,
        artifact_id=artifact.id,
        original_filename="specs.pdf",
        file_metadata={"size": 1024, "type": "pdf"},
    )
    db_session.add(attachment)

    # Project Snapshot
    snapshot = ProjectSnapshot(
        project_id=proj.id,
        generation_id=gen.id,
        version_number=1,
        manifest_location="storage/snapshots/v1.json",
    )
    db_session.add(snapshot)

    # Audit Log
    audit = AuditLog(
        action="project.create",
        resource_type="project",
        resource_id=str(proj.id),
        event_metadata={"name": "Snapshot Lab"},
    )
    db_session.add(audit)
    db_session.commit()

    assert artifact.id is not None
    assert attachment.id is not None
    assert snapshot.version_number == 1
    assert audit.action == "project.create"
