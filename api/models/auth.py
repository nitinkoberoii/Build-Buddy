"""Pydantic schemas for authentication requests and responses."""
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class RegisterRequest(BaseModel):
    """User registration payload."""
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="Account password (min 8 characters)")
    org_name: Optional[str] = Field(default=None, description="Optional custom organization name")


class LoginRequest(BaseModel):
    """User login payload."""
    email: str = Field(..., description="Account email address")
    password: str = Field(..., description="Account password")


class ForgotPasswordRequest(BaseModel):
    """Password reset request payload."""
    email: str = Field(..., description="Registered email address")


class ResetPasswordRequest(BaseModel):
    """Password reset completion payload."""
    token: str = Field(..., description="One-time password reset token")
    new_password: str = Field(..., min_length=8, description="New password (min 8 characters)")


class VerifyEmailRequest(BaseModel):
    """Email verification payload."""
    token: str = Field(..., description="One-time email verification token")


class UserResponse(BaseModel):
    """Public user identity representation."""
    id: str
    email: str
    verified: bool
    status: str
    created_at: str


class OrganizationResponse(BaseModel):
    """Organization tenant representation."""
    id: str
    name: str
    slug: str


class TokenResponse(BaseModel):
    """Authentication token response with tenant and role context."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
    organization: OrganizationResponse
    role: str
    csrf_token: str


class MessageResponse(BaseModel):
    """Simple confirmation response."""
    status: str
    message: str
