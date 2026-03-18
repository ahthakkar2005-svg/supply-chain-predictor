"""
Auth Models — Users, Roles, Tokens
All data models include tenant_id for multi-tenancy.
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ORG_ADMIN = "org_admin"
    ANALYST = "analyst"
    READ_ONLY = "read_only"


class User(BaseModel):
    """User document stored in MongoDB."""
    id: Optional[str] = None
    email: str
    hashed_password: str
    full_name: str
    role: UserRole = UserRole.READ_ONLY
    tenant_id: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserCreate(BaseModel):
    """Schema for user registration."""
    email: str
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=200)
    tenant_id: str = Field(min_length=1, max_length=100)
    role: UserRole = UserRole.READ_ONLY


class UserLogin(BaseModel):
    """Schema for login."""
    email: str
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenRefreshRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


class TokenBlacklist(BaseModel):
    """Blacklisted JWT token (for logout)."""
    jti: str  # JWT ID
    token_type: str  # "access" or "refresh"
    user_id: str
    tenant_id: str
    blacklisted_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime


class UserResponse(BaseModel):
    """Public user response (no password)."""
    id: str
    email: str
    full_name: str
    role: UserRole
    tenant_id: str
    is_active: bool
    created_at: datetime
