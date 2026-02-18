"""
API Routes for Dashboard Data
"""
from fastapi import APIRouter, Query
from typing import List, Optional
from datetime import datetime

from app.services import get_data_store
from app.models import (
    DashboardSummary, RegionRisk, RiskMetric, 
    Prediction, Alert, Supplier, NewsArticle
)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary():
    """Get executive dashboard summary with key metrics"""
    data_store = get_data_store()
    return data_store.dashboard_summary


@router.get("/regions", response_model=List[RegionRisk])
async def get_region_risks():
    """Get risk data for all geographic regions"""
    data_store = get_data_store()
    return data_store.region_risks


@router.get("/metrics", response_model=List[RiskMetric])
async def get_risk_metrics():
    """Get risk metrics by supply chain category"""
    data_store = get_data_store()
    return data_store.risk_metrics


@router.get("/time-series")
async def get_time_series_data(
    days: int = Query(default=30, ge=7, le=90, description="Number of days of historical data")
):
    """Get time series data for trend charts"""
    data_store = get_data_store()
    return data_store.time_series[-days:]


@router.get("/predictions", response_model=List[Prediction])
async def get_predictions(
    limit: int = Query(default=10, ge=1, le=50),
    risk_level: Optional[str] = Query(default=None)
):
    """Get AI-generated predictions"""
    data_store = get_data_store()
    predictions = data_store.predictions
    
    if risk_level:
        predictions = [p for p in predictions if p.risk_level.value == risk_level.lower()]
    
    return predictions[:limit]


@router.get("/alerts", response_model=List[Alert])
async def get_alerts(
    unread_only: bool = Query(default=False),
    limit: int = Query(default=10, ge=1, le=50)
):
    """Get active alerts"""
    data_store = get_data_store()
    alerts = data_store.alerts
    
    if unread_only:
        alerts = [a for a in alerts if not a.is_read]
    
    return alerts[:limit]


@router.post("/alerts/{alert_id}/read")
async def mark_alert_read(alert_id: str):
    """Mark an alert as read"""
    data_store = get_data_store()
    for alert in data_store.alerts:
        if alert.id == alert_id:
            alert.is_read = True
            return {"success": True, "message": "Alert marked as read"}
    return {"success": False, "message": "Alert not found"}


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Acknowledge an alert"""
    data_store = get_data_store()
    for alert in data_store.alerts:
        if alert.id == alert_id:
            alert.is_acknowledged = True
            alert.is_read = True
            return {"success": True, "message": "Alert acknowledged"}
    return {"success": False, "message": "Alert not found"}


@router.get("/suppliers", response_model=List[Supplier])
async def get_suppliers(
    limit: int = Query(default=15, ge=1, le=50),
    sort_by: str = Query(default="risk_score", description="Sort field: risk_score, name, tier")
):
    """Get supplier list with risk assessments"""
    data_store = get_data_store()
    suppliers = data_store.suppliers
    
    if sort_by == "name":
        suppliers = sorted(suppliers, key=lambda x: x.name)
    elif sort_by == "tier":
        suppliers = sorted(suppliers, key=lambda x: x.tier)
    # Default is already sorted by risk_score
    
    return suppliers[:limit]


@router.get("/news", response_model=List[NewsArticle])
async def get_news(
    limit: int = Query(default=20, ge=1, le=50),
    region: Optional[str] = Query(default=None)
):
    """Get latest supply chain news with analysis"""
    data_store = get_data_store()
    news = data_store.news
    
    if region:
        news = [n for n in news if n.region and region.lower() in n.region.lower()]
    
    return news[:limit]


@router.get("/ports")
async def get_ports(
    search: Optional[str] = Query(default=None, description="Search by port name or region"),
    region: Optional[str] = Query(default=None, description="Filter by region e.g. 'India'"),
):
    """Get monitored supply chain ports/hubs with live weather data"""
    from app.services.weather_service import SUPPLY_CHAIN_HUBS, get_weather_service

    weather_service = get_weather_service()
    conditions = weather_service.get_current_conditions()

    ports = []
    for hub in SUPPLY_CHAIN_HUBS:
        port_data = {
            "name": hub["name"],
            "lat": hub["lat"],
            "lon": hub["lon"],
            "region": hub["region"],
            "type": hub["type"],
            "weather": conditions.get(hub["name"], None),
        }
        ports.append(port_data)

    # Filter by region
    if region:
        ports = [p for p in ports if region.lower() in p["region"].lower()]

    # Filter by search query
    if search:
        search_lower = search.lower()
        ports = [p for p in ports if
                 search_lower in p["name"].lower() or
                 search_lower in p["region"].lower() or
                 search_lower in p["type"].lower()]

    return ports


@router.post("/refresh")
async def refresh_data():
    """Refresh all dashboard data (for demo purposes)"""
    data_store = get_data_store()
    data_store.refresh_data()
    return {
        "success": True, 
        "message": "Data refreshed",
        "timestamp": datetime.utcnow().isoformat()
    }
