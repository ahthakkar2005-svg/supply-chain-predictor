"""
Configurable Risk Model Weights — FIX 10
Dataclass stored in MongoDB with per-tenant overrides.
"""
from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, Field


class RiskModelConfig(BaseModel):
    """
    Risk model configuration — all ML coefficients that were previously hardcoded.
    Stored in MongoDB `risk_model_config` collection, one per tenant.
    """
    tenant_id: str = "default"

    # Signal weights (must sum to ~1.0)
    signal_weights: Dict[str, float] = Field(default_factory=lambda: {
        "news_sentiment": 0.25,
        "news_volume": 0.15,
        "historical_pattern": 0.20,
        "supplier_concentration": 0.15,
        "geopolitical_index": 0.15,
        "market_volatility": 0.10,
    })

    # Regional risk base scores
    regional_risk_base: Dict[str, float] = Field(default_factory=lambda: {
        "Asia Pacific": 0.55,
        "Europe": 0.40,
        "North America": 0.35,
        "Latin America": 0.45,
        "Middle East & Africa": 0.50,
    })

    # Disruption type severity multipliers
    severity_multipliers: Dict[str, float] = Field(default_factory=lambda: {
        "natural_disaster": 1.3,
        "geopolitical": 1.2,
        "economic": 1.0,
        "transportation": 0.9,
        "labor": 0.8,
        "cyber": 1.1,
        "supplier": 1.0,
        "conflict": 1.4,
    })

    # Risk level thresholds
    risk_threshold_critical: float = 0.85
    risk_threshold_high: float = 0.70
    risk_threshold_medium: float = 0.40

    # Seasonal risk ranges (months with elevated risk)
    seasonal_natural_disaster_months: list = Field(default_factory=lambda: [6, 7, 8, 9])
    seasonal_transportation_months: list = Field(default_factory=lambda: [11, 12, 1])
    seasonal_natural_disaster_factor: float = 1.3
    seasonal_transportation_factor: float = 1.2

    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[str] = None


def get_risk_config(tenant_id: str = "default") -> RiskModelConfig:
    """Load risk model config from MongoDB, or return defaults."""
    from app.core.database import get_db
    db = get_db()
    if db is not None:
        doc = db.risk_model_config.find_one({"tenant_id": tenant_id})
        if doc:
            doc.pop("_id", None)
            return RiskModelConfig(**doc)
    return RiskModelConfig(tenant_id=tenant_id)


def save_risk_config(config: RiskModelConfig) -> bool:
    """Save/update risk model config in MongoDB."""
    from app.core.database import get_db
    db = get_db()
    if db is None:
        return False

    doc = config.model_dump()
    db.risk_model_config.update_one(
        {"tenant_id": config.tenant_id},
        {"$set": doc},
        upsert=True,
    )
    return True
