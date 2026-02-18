"""
Database models for supply chain data
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DisruptionType(str, Enum):
    NATURAL_DISASTER = "natural_disaster"
    GEOPOLITICAL = "geopolitical"
    ECONOMIC = "economic"
    PANDEMIC = "pandemic"
    LABOR_STRIKE = "labor_strike"
    CYBER_ATTACK = "cyber_attack"
    TRANSPORTATION = "transportation"
    REGULATORY = "regulatory"
    SUPPLIER_FAILURE = "supplier_failure"


class Region(str, Enum):
    NA = "North America"
    EU = "Europe"
    APAC = "Asia Pacific"
    SA = "South Asia (India)"
    LATAM = "Latin America"
    MEA = "Middle East & Africa"


# Pydantic models for API
class NewsArticle(BaseModel):
    """News article data model"""
    id: str
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    source: str
    url: str
    published_at: datetime
    sentiment_score: float = Field(ge=-1.0, le=1.0, default=0.0)
    relevance_score: float = Field(ge=0.0, le=1.0, default=0.5)
    entities: List[str] = []
    disruption_type: Optional[DisruptionType] = None
    region: Optional[str] = None


class Prediction(BaseModel):
    """Supply chain disruption prediction"""
    id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    prediction_date: datetime
    risk_score: float = Field(ge=0.0, le=1.0)
    risk_level: RiskLevel
    confidence: float = Field(ge=0.0, le=1.0)
    disruption_type: DisruptionType
    region: str
    affected_categories: List[str]
    contributing_factors: List[str]
    recommended_actions: List[str]
    model_version: str = "1.0.0"


class Alert(BaseModel):
    """Alert notification model"""
    id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    title: str
    message: str
    risk_level: RiskLevel
    disruption_type: DisruptionType
    region: str
    is_read: bool = False
    is_acknowledged: bool = False
    source_predictions: List[str] = []
    expires_at: Optional[datetime] = None


class Supplier(BaseModel):
    """Supplier profile model"""
    id: str
    name: str
    region: str
    categories: List[str]
    risk_score: float = Field(ge=0.0, le=1.0, default=0.5)
    last_assessed: datetime
    tier: int = Field(ge=1, le=3, default=1)
    is_critical: bool = False


class RiskMetric(BaseModel):
    """Risk metric for dashboard"""
    category: str
    current_score: float
    previous_score: float
    trend: str  # "up", "down", "stable"
    change_percent: float


class RegionRisk(BaseModel):
    """Regional risk data for map visualization"""
    region_code: str
    region_name: str
    lat: float
    lng: float
    risk_score: float
    risk_level: RiskLevel
    active_alerts: int
    top_risks: List[str]


class DashboardSummary(BaseModel):
    """Dashboard summary data"""
    overall_risk_score: float
    overall_risk_level: RiskLevel
    risk_trend: str
    total_active_alerts: int
    critical_alerts: int
    high_alerts: int
    regions_at_risk: int
    predictions_accuracy: float
    last_updated: datetime
