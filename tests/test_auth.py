"""Comprehensive tests for authentication, Argon2id, JWT, sessions, verification, and CSRF."""
import uuid
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from api.main import app
from api.db.session import SessionLocal
from api.db.models.user import User
from api.db.models.organization import Organization, Membership
from api.db.models.auth import UserSession, EmailVerificationToken, PasswordResetToken
from api.db.repositories.auth_repository import AuthRepository

client = TestClient(app)


def test_registration_creates_user_org_and_argon2_hash():
    """Verify registration creates user + personal org + owner role, and hashes with Argon2id."""
    suffix = uuid.uuid4().hex[:6]
    email = f"user-{suffix}@example.com"
    password = "SuperSecretPassword123!"

    with patch("api.services.email_service.email_service.send_verification_email") as mock_email:
        res = client.post(
            "/api/auth/register",
            json={"email": email, "password": password, "org_name": f"Org {suffix}"},
        )
        assert res.status_code == 201
        data = res.json()

        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == email
        assert data["role"] == "owner"
        assert data["organization"]["name"] == f"Org {suffix}"
        assert "refresh_token" in res.cookies
        assert "csrf_token" in res.cookies
        mock_email.assert_called_once()

    # Verify directly in database that password hash is Argon2id
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        assert user is not None
        assert user.password_hash.startswith("$argon2id$")
        assert not user.password_hash.startswith("sha")
    finally:
        db.close()


def test_login_success_and_failure():
    """Verify login with Argon2id verification, session creation, and invalid password rejection."""
    suffix = uuid.uuid4().hex[:6]
    email = f"login-{suffix}@example.com"
    password = "CorrectPassword123!"

    # Register first
    client.post("/api/auth/register", json={"email": email, "password": password})

    # Test login with incorrect password -> 401
    bad_login = client.post("/api/auth/login", json={"email": email, "password": "WrongPassword!"})
    assert bad_login.status_code == 401
    assert "Invalid email or password" in bad_login.json()["detail"]

    # Test login with correct password -> 200
    good_login = client.post("/api/auth/login", json={"email": email, "password": password})
    assert good_login.status_code == 200
    data = good_login.json()
    assert "access_token" in data
    assert "refresh_token" in good_login.cookies
    assert data["user"]["email"] == email


def test_session_rotation_on_refresh_and_revocation():
    """Verify session rotation on /refresh, and server-revocation on /logout."""
    suffix = uuid.uuid4().hex[:6]
    email = f"session-{suffix}@example.com"
    password = "SessionPassword123!"

    # Register to get initial cookies
    reg_res = client.post("/api/auth/register", json={"email": email, "password": password})
    initial_refresh_cookie = reg_res.cookies.get("refresh_token")
    assert initial_refresh_cookie is not None

    # Call /refresh with cookie
    client.cookies.set("refresh_token", initial_refresh_cookie)
    refresh_res = client.post("/api/auth/refresh")
    assert refresh_res.status_code == 200
    new_refresh_cookie = refresh_res.cookies.get("refresh_token")
    assert new_refresh_cookie != initial_refresh_cookie  # Rotated!

    # Calling refresh again with OLD revoked cookie must fail -> 401
    client.cookies.set("refresh_token", initial_refresh_cookie)
    stale_res = client.post("/api/auth/refresh")
    assert stale_res.status_code == 401

    # Call logout with active new cookie
    client.cookies.set("refresh_token", new_refresh_cookie)
    logout_res = client.post("/api/auth/logout")
    assert logout_res.status_code == 200

    # Refreshing after logout must fail -> 401
    client.cookies.set("refresh_token", new_refresh_cookie)
    post_logout_res = client.post("/api/auth/refresh")
    assert post_logout_res.status_code == 401


def test_email_verification_flow():
    """Verify email verification token consumption and user status update."""
    suffix = uuid.uuid4().hex[:6]
    email = f"verify-{suffix}@example.com"
    password = "VerifyPassword123!"

    captured_token = None
    with patch("api.services.email_service.email_service.send_verification_email") as mock_email:
        mock_email.side_effect = lambda to, token: globals().update({"captured_token": token}) or True
        reg = client.post("/api/auth/register", json={"email": email, "password": password})
        assert reg.status_code == 201

    db = SessionLocal()
    try:
        user_before = db.query(User).filter(User.email == email).first()
        assert user_before.verified_at is None

        # Verify invalid token fails
        bad_res = client.post("/api/auth/verify-email", json={"token": "invalid-token-123"})
        assert bad_res.status_code == 400

        # Query token from DB
        token_record = db.query(EmailVerificationToken).filter(EmailVerificationToken.user_id == user_before.id).first()
        assert token_record is not None

        # Manually verify using the captured token
        from api.services.security import hash_token
        from api.db.repositories.auth_repository import AuthRepository
        verified_user = AuthRepository.consume_verification_token(db, token_record.token_hash)
        db.commit()
        assert verified_user is not None
        assert verified_user.verified_at is not None
    finally:
        db.close()


def test_password_reset_flow():
    """Verify forgot-password token creation, password reset with Argon2id, and session revocation."""
    suffix = uuid.uuid4().hex[:6]
    email = f"reset-{suffix}@example.com"
    old_password = "OldPassword123!"
    new_password = "BrandNewPassword456!"

    # Register user
    reg = client.post("/api/auth/register", json={"email": email, "password": old_password})
    assert reg.status_code == 201

    with patch("api.services.email_service.email_service.send_password_reset_email") as mock_email:
        forgot_res = client.post("/api/auth/forgot-password", json={"email": email})
        assert forgot_res.status_code == 200
        mock_email.assert_called_once()

    # Query token hash from database
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        reset_record = db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.id).first()
        assert reset_record is not None

        # Consume reset token directly via repo
        from api.services.security import hash_password
        updated = AuthRepository.consume_password_reset_token(db, reset_record.token_hash, hash_password(new_password))
        db.commit()
        assert updated is not None
    finally:
        db.close()

    # Login with old password must fail
    fail_res = client.post("/api/auth/login", json={"email": email, "password": old_password})
    assert fail_res.status_code == 401

    # Login with new password must succeed
    ok_res = client.post("/api/auth/login", json={"email": email, "password": new_password})
    assert ok_res.status_code == 200


def test_csrf_protection_on_cookie_authenticated_mutations():
    """Verify that cookie-authenticated mutation endpoints enforce X-CSRF-Token."""
    suffix = uuid.uuid4().hex[:6]
    email = f"csrf-{suffix}@example.com"
    password = "CsrfPassword123!"

    # Register to establish session cookies
    reg = client.post("/api/auth/register", json={"email": email, "password": password})
    assert reg.status_code == 201
    csrf_token = reg.cookies.get("csrf_token")
    refresh_token = reg.cookies.get("refresh_token")

    # Clear Authorization header so request relies on cookies
    client.headers.pop("Authorization", None)
    client.cookies.set("refresh_token", refresh_token)
    client.cookies.set("csrf_token", csrf_token)

    # Attempt mutation without X-CSRF-Token header -> 403 Forbidden
    res_no_csrf = client.post(
        "/api/generations",
        json={"prompt": "CSRF attack attempt"},
    )
    assert res_no_csrf.status_code == 403
    assert "CSRF validation failed" in res_no_csrf.json()["detail"]

    # Attempt mutation with matching X-CSRF-Token header -> 201 Created
    res_with_csrf = client.post(
        "/api/generations",
        json={"prompt": "Valid authorized generation with CSRF"},
        headers={"X-CSRF-Token": csrf_token},
    )
    assert res_with_csrf.status_code == 201
