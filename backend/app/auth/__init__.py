"""Auth module — JWT authentication & RBAC"""
from .models import User, UserRole, TokenBlacklist, UserCreate, UserLogin, TokenResponse
from .utils import create_access_token, create_refresh_token, verify_token, hash_password, verify_password
from .dependencies import get_current_user, require_role, get_current_active_user

__all__ = [
    "User", "UserRole", "TokenBlacklist", "UserCreate", "UserLogin", "TokenResponse",
    "create_access_token", "create_refresh_token", "verify_token",
    "hash_password", "verify_password",
    "get_current_user", "require_role", "get_current_active_user",
]
