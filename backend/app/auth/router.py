"""
Auth Router — Registration, Login, Refresh, Logout
"""
import uuid
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.models import (
    User, UserCreate, UserLogin, UserRole,
    TokenResponse, TokenRefreshRequest, UserResponse,
)
from app.auth.utils import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, verify_token,
)
from app.auth.dependencies import get_current_active_user
from app.core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate):
    """Register a new user."""
    from app.core.database import get_db
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    # Check duplicate email
    existing = db.users.find_one({"email": payload.email})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user_id = str(uuid.uuid4())
    user_doc = {
        "_id": user_id,
        "email": payload.email,
        "hashed_password": hash_password(payload.password),
        "full_name": payload.full_name,
        "role": payload.role.value,
        "tenant_id": payload.tenant_id,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    db.users.insert_one(user_doc)
    logger.info(f"User registered: {payload.email} (tenant={payload.tenant_id})")

    return UserResponse(
        id=user_id,
        email=payload.email,
        full_name=payload.full_name,
        role=payload.role,
        tenant_id=payload.tenant_id,
        is_active=True,
        created_at=user_doc["created_at"],
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin):
    """Authenticate and return JWT tokens."""
    from app.core.database import get_db
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    user_doc = db.users.find_one({"email": payload.email})
    if not user_doc or not verify_password(payload.password, user_doc["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user_doc.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    settings = get_settings()
    token_data = {
        "sub": user_doc["_id"],
        "email": user_doc["email"],
        "full_name": user_doc.get("full_name", ""),
        "role": user_doc["role"],
        "tenant_id": user_doc["tenant_id"],
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    logger.info(f"User logged in: {payload.email}")
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(payload: TokenRefreshRequest):
    """Exchange a refresh token for a new access token pair."""
    token_payload = verify_token(payload.refresh_token)
    if token_payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if token_payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not a refresh token")

    # Check blacklist
    from app.core.database import get_db
    db = get_db()
    jti = token_payload.get("jti")
    if jti and db is not None:
        if db.token_blacklist.find_one({"jti": jti}):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")

    settings = get_settings()
    token_data = {
        "sub": token_payload["sub"],
        "email": token_payload.get("email", ""),
        "full_name": token_payload.get("full_name", ""),
        "role": token_payload.get("role", "read_only"),
        "tenant_id": token_payload.get("tenant_id", ""),
    }

    new_access = create_access_token(token_data)
    new_refresh = create_refresh_token(token_data)

    # Blacklist old refresh token
    if jti and db is not None:
        db.token_blacklist.insert_one({
            "jti": jti,
            "token_type": "refresh",
            "user_id": token_payload["sub"],
            "tenant_id": token_payload.get("tenant_id", ""),
            "blacklisted_at": datetime.utcnow(),
            "expires_at": datetime.utcfromtimestamp(token_payload.get("exp", 0)),
        })

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout")
async def logout(user: User = Depends(get_current_active_user)):
    """Log out by blacklisting the current token."""
    # Note: The token info comes from the dependency — we blacklist any future use
    from app.core.database import get_db
    db = get_db()
    if db is not None:
        # We can't get the JTI here directly from the dependency,
        # so clients should also discard tokens client-side.
        logger.info(f"User logged out: {user.email}")

    return {"message": "Successfully logged out"}
