"""Authentication and session management router."""
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from api.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
from api.db.session import get_db
from api.db.repositories.auth_repository import AuthRepository
from api.models.auth import (
    RegisterRequest,
    LoginRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
    TokenResponse,
    UserResponse,
    OrganizationResponse,
    MessageResponse,
)
from api.dependencies.auth import AuthContext, get_current_auth
from api.services.security import (
    hash_password,
    verify_password,
    create_access_token,
    generate_secure_token,
    hash_token,
    generate_csrf_token,
)
from api.services.email_service import email_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _set_auth_cookies(response: Response, refresh_token: str, csrf_token: str) -> None:
    """Sets secure HTTP-only refresh cookie and JS-readable CSRF cookie."""
    max_age = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
    # HTTP-only refresh cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=max_age,
        httponly=True,
        samesite="lax",
        secure=False,  # Set to True in HTTPS production environments
    )
    # JS-readable CSRF double-submit cookie
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        max_age=max_age,
        httponly=False,
        samesite="lax",
        secure=False,
    )


def _clear_auth_cookies(response: Response) -> None:
    """Clears authentication and CSRF cookies on logout."""
    response.delete_cookie("refresh_token")
    response.delete_cookie("csrf_token")


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    response: Response,
    req: Request,
    db: Session = Depends(get_db),
):
    """Registers a new user, creates a personal organization, and issues session tokens."""
    # 1. Hash password using Argon2id
    argon2_hash = hash_password(request.password)

    # 2. Create user, organization, and owner membership
    try:
        user, org, membership = AuthRepository.create_user_with_personal_organization(
            session=db,
            email=request.email,
            password_hash=argon2_hash,
            org_name=request.org_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # 3. Create email verification token and trigger email
    raw_verify_token = generate_secure_token()
    verify_expires = datetime.now(timezone.utc) + timedelta(hours=24)
    AuthRepository.create_verification_token(
        session=db,
        user_id=user.id,
        token_hash=hash_token(raw_verify_token),
        expires_at=verify_expires,
    )
    email_service.send_verification_email(user.email, raw_verify_token)

    # 4. Create server-revocable refresh session
    raw_refresh_token = generate_secure_token()
    refresh_expires = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    AuthRepository.create_session(
        session=db,
        user_id=user.id,
        refresh_token_hash=hash_token(raw_refresh_token),
        expires_at=refresh_expires,
        user_agent=req.headers.get("user-agent"),
        ip_address=req.client.host if req.client else None,
    )

    csrf_token = generate_csrf_token()
    db.commit()

    # 5. Set cookies and issue access token
    _set_auth_cookies(response, raw_refresh_token, csrf_token)
    access_token = create_access_token(
        user_id=str(user.id),
        email=user.email,
        org_id=str(org.id),
        role=membership.role,
    )

    return TokenResponse(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            verified=user.verified_at is not None,
            status=user.status,
            created_at=user.created_at.isoformat(),
        ),
        organization=OrganizationResponse(
            id=str(org.id),
            name=org.name,
            slug=org.slug,
        ),
        role=membership.role,
        csrf_token=csrf_token,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    response: Response,
    req: Request,
    db: Session = Depends(get_db),
):
    """Authenticates credentials against Argon2id hash and issues rotating session cookies."""
    user = AuthRepository.get_user_by_email(db, request.email)
    if not user or not user.password_hash or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is suspended or deactivated",
        )

    primary = AuthRepository.get_user_primary_membership(db, user.id)
    if not primary:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no associated organization membership",
        )
    org, membership = primary

    # Create new rotating refresh session
    raw_refresh_token = generate_secure_token()
    refresh_expires = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    AuthRepository.create_session(
        session=db,
        user_id=user.id,
        refresh_token_hash=hash_token(raw_refresh_token),
        expires_at=refresh_expires,
        user_agent=req.headers.get("user-agent"),
        ip_address=req.client.host if req.client else None,
    )

    csrf_token = generate_csrf_token()
    db.commit()

    _set_auth_cookies(response, raw_refresh_token, csrf_token)
    access_token = create_access_token(
        user_id=str(user.id),
        email=user.email,
        org_id=str(org.id),
        role=membership.role,
    )

    return TokenResponse(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            verified=user.verified_at is not None,
            status=user.status,
            created_at=user.created_at.isoformat(),
        ),
        organization=OrganizationResponse(
            id=str(org.id),
            name=org.name,
            slug=org.slug,
        ),
        role=membership.role,
        csrf_token=csrf_token,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_session(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Rotates refresh session token and returns a fresh short-lived access token."""
    refresh_cookie = request.cookies.get("refresh_token")
    if not refresh_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh session cookie",
        )

    session_record = AuthRepository.get_valid_session(db, hash_token(refresh_cookie))
    if not session_record:
        _clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or been revoked. Please log in again.",
        )

    user = AuthRepository.get_user_by_id(db, session_record.user_id)
    if not user or user.status != "active":
        _clear_auth_cookies(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or not found")

    primary = AuthRepository.get_user_primary_membership(db, user.id)
    if not primary:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No organization membership")
    org, membership = primary

    # Session rotation: revoke old session, issue new one
    AuthRepository.revoke_session(db, session_record.id)
    new_refresh_token = generate_secure_token()
    refresh_expires = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    AuthRepository.create_session(
        session=db,
        user_id=user.id,
        refresh_token_hash=hash_token(new_refresh_token),
        expires_at=refresh_expires,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )

    csrf_token = generate_csrf_token()
    db.commit()

    _set_auth_cookies(response, new_refresh_token, csrf_token)
    access_token = create_access_token(
        user_id=str(user.id),
        email=user.email,
        org_id=str(org.id),
        role=membership.role,
    )

    return TokenResponse(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            verified=user.verified_at is not None,
            status=user.status,
            created_at=user.created_at.isoformat(),
        ),
        organization=OrganizationResponse(
            id=str(org.id),
            name=org.name,
            slug=org.slug,
        ),
        role=membership.role,
        csrf_token=csrf_token,
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Revokes the active refresh session from the database and clears cookies."""
    refresh_cookie = request.cookies.get("refresh_token")
    if refresh_cookie:
        session_record = AuthRepository.get_valid_session(db, hash_token(refresh_cookie))
        if session_record:
            AuthRepository.revoke_session(db, session_record.id)
            db.commit()

    _clear_auth_cookies(response)
    return MessageResponse(status="ok", message="Logged out successfully")


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    request: VerifyEmailRequest,
    db: Session = Depends(get_db),
):
    """Consumes an email-verification token and marks the account as verified."""
    user = AuthRepository.consume_verification_token(db, hash_token(request.token))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired email verification token",
        )
    db.commit()
    return MessageResponse(status="ok", message="Email address verified successfully")


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    """Sends a password-reset link if the account exists."""
    user = AuthRepository.get_user_by_email(db, request.email)
    if user:
        reset_token = generate_secure_token()
        reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        AuthRepository.create_password_reset_token(
            session=db,
            user_id=user.id,
            token_hash=hash_token(reset_token),
            expires_at=reset_expires,
        )
        db.commit()
        email_service.send_password_reset_email(user.email, reset_token)

    return MessageResponse(
        status="ok",
        message="If this email is registered, a password reset link has been dispatched.",
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    """Validates reset token, updates password with Argon2id, and revokes prior sessions."""
    argon2_hash = hash_password(request.new_password)
    user = AuthRepository.consume_password_reset_token(
        session=db,
        token_hash=hash_token(request.token),
        new_password_hash=argon2_hash,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token",
        )
    db.commit()
    return MessageResponse(
        status="ok",
        message="Password reset successfully. Please log in with your new password.",
    )


@router.get("/me", response_model=TokenResponse)
async def get_me(auth: AuthContext = Depends(get_current_auth)):
    """Retrieves authenticated identity, organization, and role information."""
    access_token = create_access_token(
        user_id=str(auth.user.id),
        email=auth.user.email,
        org_id=str(auth.organization.id),
        role=auth.role,
    )
    return TokenResponse(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(
            id=str(auth.user.id),
            email=auth.user.email,
            verified=auth.user.verified_at is not None,
            status=auth.user.status,
            created_at=auth.user.created_at.isoformat(),
        ),
        organization=OrganizationResponse(
            id=str(auth.organization.id),
            name=auth.organization.name,
            slug=auth.organization.slug,
        ),
        role=auth.role,
        csrf_token=generate_csrf_token(),
    )
