"""Authentication and tenancy context dependency for FastAPI."""
import uuid
from typing import Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
from fastapi import Depends, HTTPException, Header, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.db.session import get_db
from api.db.models.user import User
from api.db.models.organization import Organization, Membership
from api.db.models.auth import UserSession
from api.db.repositories.auth_repository import AuthRepository
from api.services.security import (
    decode_access_token,
    hash_token,
    verify_csrf_token,
)


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
    request: Request,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_user_email: Optional[str] = Header(None, alias="X-User-Email"),
    x_csrf_token: Optional[str] = Header(None, alias="X-CSRF-Token"),
    db: Session = Depends(get_db),
) -> AuthContext:
    """Resolves authenticated user and tenant organization from JWT, cookie sessions, or dev context.
    
    Security: Never trusts client-supplied user_id or organization_id in request bodies.
    """
    # 1. Bearer Token resolution (JWT or test email)
    if authorization and authorization.startswith("Bearer "):
        raw_token = authorization.replace("Bearer ", "").strip()
        if "@" in raw_token:
            # Test helper: Bearer email
            user = AuthRepository.get_user_by_email(db, raw_token)
            if not user:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid test token email")
            primary = AuthRepository.get_user_primary_membership(db, user.id)
            if not primary:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has no organization membership")
            return AuthContext(user=user, organization=primary[0], membership=primary[1])

        try:
            payload = decode_access_token(raw_token)
            user_id = uuid.UUID(payload["sub"])
            org_id = uuid.UUID(payload["org_id"])
            user = AuthRepository.get_user_by_id(db, user_id)
            if not user or user.status != "active":
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or not found")

            # Verify membership in token org
            stmt_mem = select(Membership).where(
                Membership.user_id == user_id,
                Membership.organization_id == org_id,
            )
            membership = db.execute(stmt_mem).scalar_one_or_none()
            if not membership:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Revoked or invalid organization membership")

            stmt_org = select(Organization).where(Organization.id == org_id)
            org = db.execute(stmt_org).scalar_one()

            return AuthContext(user=user, organization=org, membership=membership)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid or expired access token: {e}")

    # 2. X-User-Email Header (for deterministic tests)
    if x_user_email:
        user = AuthRepository.get_user_by_email(db, x_user_email)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"User '{x_user_email}' not found")
        primary = AuthRepository.get_user_primary_membership(db, user.id)
        if not primary:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has no organization membership")
        return AuthContext(user=user, organization=primary[0], membership=primary[1])

    # 3. HTTP-Only Cookie Session Resolution
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        # Enforce CSRF protection on mutating cookie-authenticated endpoints
        if request.method in ("POST", "PUT", "DELETE", "PATCH"):
            cookie_csrf = request.cookies.get("csrf_token")
            if not verify_csrf_token(cookie_csrf, x_csrf_token):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CSRF validation failed: missing or mismatched X-CSRF-Token",
                )

        session_record = AuthRepository.get_valid_session(db, hash_token(refresh_token))
        if session_record:
            user = AuthRepository.get_user_by_id(db, session_record.user_id)
            if user and user.status == "active":
                primary = AuthRepository.get_user_primary_membership(db, user.id)
                if primary:
                    return AuthContext(user=user, organization=primary[0], membership=primary[1])

    # 4. Fallback to default auth context for local dev browser UI before login screen
    return get_or_create_default_auth(db)


def require_modify_permission(auth: AuthContext = Depends(get_current_auth)) -> AuthContext:
    """Guards endpoints from read-only viewers."""
    if not auth.can_modify():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Viewer role has read-only access",
        )
    return auth
