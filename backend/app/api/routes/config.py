"""
Config API Routes — FIX 10
GET/PUT /api/v1/config/risk-model
"""
from fastapi import APIRouter, Depends
from datetime import datetime

from app.auth.dependencies import get_current_active_user, require_role
from app.auth.models import User, UserRole
from app.models.risk_config import RiskModelConfig, get_risk_config, save_risk_config

router = APIRouter(prefix="/api/v1/config", tags=["Configuration"])


@router.get("/risk-model", response_model=RiskModelConfig)
async def get_risk_model_config(
    user: User = Depends(get_current_active_user),
):
    """Get the risk model configuration for the current tenant."""
    return get_risk_config(tenant_id=user.tenant_id)


@router.put("/risk-model", response_model=RiskModelConfig)
async def update_risk_model_config(
    config: RiskModelConfig,
    user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN])),
):
    """Update risk model configuration (OrgAdmin+ only)."""
    config.tenant_id = user.tenant_id
    config.updated_at = datetime.utcnow()
    config.updated_by = user.id

    success = save_risk_config(config)
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Failed to save configuration")

    # Write audit log
    from app.core.database import get_db
    import uuid
    db = get_db()
    if db:
        db.audit_logs.insert_one({
            "_id": str(uuid.uuid4()),
            "user_id": user.id,
            "user_email": user.email,
            "tenant_id": user.tenant_id,
            "action": "config.risk_model.update",
            "resource_type": "risk_model_config",
            "resource_id": user.tenant_id,
            "timestamp": datetime.utcnow(),
            "result": "success",
        })

    return config
