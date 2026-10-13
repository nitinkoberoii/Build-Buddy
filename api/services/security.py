"""Security utilities: Argon2id password hashing, JWT access tokens, and CSRF protection."""
import hmac
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from argon2 import PasswordHasher, Type
from argon2.exceptions import VerifyMismatchError, InvalidHashError

from api.config import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

# Argon2id password hasher configuration (OWASP recommended parameters)
ph = PasswordHasher(
    time_cost=2,
    memory_cost=19456,  # ~19 MiB
    parallelism=1,
    hash_len=32,
    type=Type.ID,
)


def hash_password(password: str) -> str:
    """Hashes a plaintext password using Argon2id."""
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against an Argon2id hash."""
    if not hashed_password:
        return False
    try:
        return ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def create_access_token(
    user_id: str,
    email: str,
    org_id: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Generates a signed, short-lived JWT access token."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {
        "sub": user_id,
        "email": email,
        "org_id": org_id,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes and validates a JWT access token. Raises jwt exceptions on failure."""
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])


def generate_secure_token() -> str:
    """Generates a cryptographically random URL-safe token for sessions, email, and password resets."""
    return secrets.token_urlsafe(32)


def hash_token(raw_token: str) -> str:
    """Hashes a high-entropy secret token before storing it in the database."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def generate_csrf_token() -> str:
    """Generates a random CSRF token to accompany cookie sessions."""
    return secrets.token_urlsafe(32)


def verify_csrf_token(cookie_csrf: Optional[str], header_csrf: Optional[str]) -> bool:
    """Validates double-submit CSRF cookie against request header using constant-time comparison."""
    if not cookie_csrf or not header_csrf:
        return False
    return hmac.compare_digest(cookie_csrf, header_csrf)
