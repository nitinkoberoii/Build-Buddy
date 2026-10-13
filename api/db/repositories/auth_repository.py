"""Repository for authentication, users, organizations, sessions, and tokens."""
import uuid
import re
from datetime import datetime, timezone
from typing import Optional, Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.db.models.user import User
from api.db.models.organization import Organization, Membership
from api.db.models.auth import UserSession, EmailVerificationToken, PasswordResetToken


class AuthRepository:
    """Data access repository for Authentication operations."""

    @staticmethod
    def get_user_by_email(session: Session, email: str) -> Optional[User]:
        """Finds a user by email (case-insensitive)."""
        stmt = select(User).where(User.email == email.strip().lower())
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_user_by_id(session: Session, user_id: uuid.UUID) -> Optional[User]:
        """Finds a user by UUID."""
        stmt = select(User).where(User.id == user_id)
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_user_primary_membership(session: Session, user_id: uuid.UUID) -> Optional[Tuple[Organization, Membership]]:
        """Retrieves the active organization and membership for a user."""
        stmt = (
            select(Organization, Membership)
            .join(Membership, Organization.id == Membership.organization_id)
            .where(Membership.user_id == user_id)
            .order_by(Membership.created_at)
        )
        result = session.execute(stmt).first()
        if result:
            return result[0], result[1]
        return None

    @classmethod
    def create_user_with_personal_organization(
        cls,
        session: Session,
        email: str,
        password_hash: str,
        org_name: Optional[str] = None,
    ) -> Tuple[User, Organization, Membership]:
        """Creates a user plus their personal organization and owner membership."""
        normalized_email = email.strip().lower()
        if cls.get_user_by_email(session, normalized_email):
            raise ValueError(f"An account with email '{normalized_email}' already exists.")

        # 1. Create User
        user = User(
            id=uuid.uuid4(),
            email=normalized_email,
            password_hash=password_hash,
            status="active",
        )
        session.add(user)
        session.flush()

        # 2. Derive personal organization slug
        email_prefix = normalized_email.split("@")[0]
        base_slug = re.sub(r"[^a-z0-9-]", "-", email_prefix).strip("-") or "workspace"
        unique_slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"
        resolved_name = org_name or f"{email_prefix}'s Team"

        org = Organization(
            id=uuid.uuid4(),
            name=resolved_name,
            slug=unique_slug,
        )
        session.add(org)
        session.flush()

        # 3. Create Owner Membership
        membership = Membership(
            id=uuid.uuid4(),
            user_id=user.id,
            organization_id=org.id,
            role="owner",
        )
        session.add(membership)
        session.flush()

        return user, org, membership

    @staticmethod
    def create_session(
        session: Session,
        user_id: uuid.UUID,
        refresh_token_hash: str,
        expires_at: datetime,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> UserSession:
        """Creates a new server-revocable user session."""
        user_session = UserSession(
            id=uuid.uuid4(),
            user_id=user_id,
            refresh_token_hash=refresh_token_hash,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=expires_at,
        )
        session.add(user_session)
        session.flush()
        return user_session

    @staticmethod
    def get_valid_session(session: Session, refresh_token_hash: str) -> Optional[UserSession]:
        """Finds an unrevoked, unexpired session matching the refresh token hash."""
        now = datetime.now(timezone.utc)
        stmt = select(UserSession).where(
            UserSession.refresh_token_hash == refresh_token_hash,
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > now,
        )
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def revoke_session(session: Session, session_id: uuid.UUID) -> None:
        """Revokes a session by ID."""
        stmt = select(UserSession).where(UserSession.id == session_id)
        user_session = session.execute(stmt).scalar_one_or_none()
        if user_session and not user_session.revoked_at:
            user_session.revoked_at = datetime.now(timezone.utc)
            session.flush()

    @staticmethod
    def revoke_all_user_sessions(session: Session, user_id: uuid.UUID) -> None:
        """Revokes all active sessions for a user (e.g. after password reset)."""
        now = datetime.now(timezone.utc)
        stmt = select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.revoked_at.is_(None),
        )
        active_sessions = session.execute(stmt).scalars().all()
        for s in active_sessions:
            s.revoked_at = now
        session.flush()

    @staticmethod
    def create_verification_token(
        session: Session,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> EmailVerificationToken:
        """Persists an email-verification token."""
        token_record = EmailVerificationToken(
            id=uuid.uuid4(),
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        session.add(token_record)
        session.flush()
        return token_record

    @staticmethod
    def consume_verification_token(session: Session, token_hash: str) -> Optional[User]:
        """Validates, consumes an email-verification token, and sets user verified_at."""
        now = datetime.now(timezone.utc)
        stmt = select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == token_hash,
            EmailVerificationToken.used_at.is_(None),
            EmailVerificationToken.expires_at > now,
        )
        record = session.execute(stmt).scalar_one_or_none()
        if not record:
            return None

        record.used_at = now
        stmt_user = select(User).where(User.id == record.user_id)
        user = session.execute(stmt_user).scalar_one_or_none()
        if user:
            user.verified_at = now
            session.flush()
        return user

    @staticmethod
    def create_password_reset_token(
        session: Session,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> PasswordResetToken:
        """Persists a password-reset token."""
        token_record = PasswordResetToken(
            id=uuid.uuid4(),
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        session.add(token_record)
        session.flush()
        return token_record

    @staticmethod
    def consume_password_reset_token(
        session: Session,
        token_hash: str,
        new_password_hash: str,
    ) -> Optional[User]:
        """Validates reset token, updates password, and revokes prior sessions."""
        now = datetime.now(timezone.utc)
        stmt = select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > now,
        )
        record = session.execute(stmt).scalar_one_or_none()
        if not record:
            return None

        record.used_at = now
        stmt_user = select(User).where(User.id == record.user_id)
        user = session.execute(stmt_user).scalar_one_or_none()
        if user:
            user.password_hash = new_password_hash
            # Revoke all existing sessions
            AuthRepository.revoke_all_user_sessions(session, user.id)
            session.flush()
        return user
