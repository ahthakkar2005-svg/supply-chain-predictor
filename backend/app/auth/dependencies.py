"""
Auth Dependencies — FastAPI dependency injection for authentication & RBAC
"""
import logging
from typing import List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.auth.models import User, UserRole
from app.auth.utils import verify_token

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[User]:
    """
    Extract and validate the current user from the JWT bearer token.
    Returns None if no token is provided (for optional auth endpoints).
    """
    if token is None:
        return None

    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type — use access token",
        )

    # Check blacklist
    from app.core.database import get_db
    db = get_db()
    jti = payload.get("jti")
    if jti and db is not None:
        blacklisted = db.token_blacklist.find_one({"jti": jti})
        if blacklisted:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
            )

    # Load user from DB
    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    if db is not None:
        user_doc = db.users.find_one({"_id": user_id})
        if user_doc:
            user_doc["id"] = user_doc.pop("_id")
            return User(**user_doc)

    # Fallback: construct user from token payload
    return User(
        id=user_id,
        email=payload.get("email", ""),
        hashed_password="",
        full_name=payload.get("full_name", ""),
        role=UserRole(payload.get("role", "read_only")),
        tenant_id=tenant_id or "",
    )


async def get_current_active_user(user: Optional[User] = Depends(get_current_user)) -> User:
    """Require an authenticated, active user."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is disabled")
    return user


def require_role(allowed_roles: List[UserRole]):
    """
    FastAPI dependency factory — enforces RBAC.
    Usage: Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN]))
    """
    async def _check(user: User = Depends(get_current_active_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {[r.value for r in allowed_roles]}",
            )
        return user
    return _check


def require_tenant():
    """
    Dependency that enforces tenant isolation.
    Returns the tenant_id of the authenticated user.
    """
    async def _check(user: User = Depends(get_current_active_user)) -> str:
        if not user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not associated with any tenant",
            )
        return user.tenant_id
    return _check
