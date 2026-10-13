"""Authentication and tenancy context dependency for FastAPI."""
import uuid
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum
from fastapi import Depends, HTTPException, Header, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.db.session import get_db
from api.db.models.user import User
from api.db.models.organization import Organization, Membership
from api.db.models.project import Project


class Role(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


@dataclass
class AuthContext:
    """Authenticated context carrying identity, tenancy, and organization role."""
    user: User
    organization: Organization
    membership: Membership

    @property
    def role(self) -> str:
        return self.membership.role

    def is_viewer(self) -> bool:
        return self.role == Role.VIEWER.value

    def can_modify(self) -> bool:
        """Members, admins, and owners can modify resources."""
        return self.role in (Role.MEMBER.value, Role.ADMIN.value, Role.OWNER.value)

    def can_manage_members(self) -> bool:
        """Admins and owners can manage members."""
        return self.role in (Role.ADMIN.value, Role.OWNER.value)

    def can_manage_organization(self) -> bool:
        """Only owners can manage root organization settings and deletion."""
        return self.role == Role.OWNER.value


def get_or_create_default_auth(db: Session) -> AuthContext:
    """Provides a default authenticated owner context for unauthenticated local browser clients."""
    # Find or create default user
    stmt = select(User).where(User.email == "developer@buildbuddy.local")
    user = db.execute(stmt).scalar_one_or_none()
    if not user:
        user = User(
            id=uuid.uuid4(),
            email="developer@buildbuddy.local",
            status="active",
        )
        db.add(user)
        db.flush()

    # Find or create default organization
    stmt_org = select(Organization).where(Organization.slug == "default")
    org = db.execute(stmt_org).scalar_one_or_none()
    if not org:
        org = Organization(
            id=uuid.uuid4(),
            name="Default Workspace",
            slug="default",
        )
        db.add(org)
        db.flush()

    # Find or create owner membership
    stmt_mem = select(Membership).where(
        Membership.user_id == user.id,
        Membership.organization_id == org.id,
    )
    membership = db.execute(stmt_mem).scalar_one_or_none()
    if not membership:
        membership = Membership(
            id=uuid.uuid4(),
            user_id=user.id,
            organization_id=org.id,
            role=Role.OWNER.value,
        )
        db.add(membership)
        db.flush()

    db.commit()
    return AuthContext(user=user, organization=org, membership=membership)


def get_current_auth(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_user_email: Optional[str] = Header(None, alias="X-User-Email"),
    db: Session = Depends(get_db),
) -> AuthContext:
    """Resolves authenticated user and tenant organization from headers or default context.
    
    Security: Never trusts client-supplied user_id or organization_id in request payloads.
    """
    email_to_lookup: Optional[str] = None

    if x_user_email:
        email_to_lookup = x_user_email.strip()
    elif authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "").strip()
        # Allows Bearer email or Bearer user token
        if "@" in token:
            email_to_lookup = token

    if email_to_lookup:
        stmt = select(User).where(User.email == email_to_lookup)
        user = db.execute(stmt).scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"User '{email_to_lookup}' not found or invalid credentials",
            )

        # Lookup organization membership for this user
        stmt_mem = select(Membership).where(Membership.user_id == user.id)
        membership = db.execute(stmt_mem).scalar_one_or_none()
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no organization membership",
            )

        stmt_org = select(Organization).where(Organization.id == membership.organization_id)
        org = db.execute(stmt_org).scalar_one()

        return AuthContext(user=user, organization=org, membership=membership)

    # Fallback to default auth context for local dev web UI before login screen
    return get_or_create_default_auth(db)


def require_modify_permission(auth: AuthContext = Depends(get_current_auth)) -> AuthContext:
    """Guards endpoints from read-only viewers."""
    if not auth.can_modify():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Viewer role has read-only access",
        )
    return auth
