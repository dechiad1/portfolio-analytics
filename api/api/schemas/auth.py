from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Request schema for user registration."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    """Request schema for user login."""

    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    """Response schema for successful authentication."""

    user_id: UUID
    email: str
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Response schema for user info."""

    id: UUID
    email: str
    created_at: datetime
    is_admin: bool = False
