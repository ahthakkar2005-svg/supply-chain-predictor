"""
API Routes for Dashboard Data
"""
from fastapi import APIRouter, Query
from typing import List, Optional
from datetime import datetime

from app.core.database import get_async_collection
from app.models.db_models import (
    doc_to_dashboard_summary, doc_to_region_risk, doc_to_risk_metric,
    doc_to_prediction, doc_to_alert, doc_to_supplier, doc_to_news
)
from app.models import (
    DashboardSummary, RegionRisk, RiskMetric, 
    Prediction, Alert, Supplier, NewsArticle
)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary():
    db = await get_async_collection("dashboard_summary")
    doc = await db.find_one()
    return doc_to_dashboard_summary(doc) if doc else None


@router.get("/regions", response_model=List[RegionRisk])
async def get_region_risks():
    """Get risk data for all geographic regions"""
    db = await get_async_collection("region_risks")
    docs = await db.find().to_list(length=100)
    return [doc_to_region_risk(d) for d in docs]


@router.get("/metrics", response_model=List[RiskMetric])
async def get_risk_metrics():
    """Get risk metrics by supply chain category"""
    db = await get_async_collection("risk_metrics")
    docs = await db.find().to_list(length=100)
    return [doc_to_risk_metric(d) for d in docs]


@router.get("/time-series")
async def get_time_series_data(
    days: int = Query(default=30, ge=7, le=90, description="Number of days of historical data")
):
    """Get time series data for trend charts"""
    db = await get_async_collection("time_series")
    pipeline = [{"$sort": {"date": 1}}, {"$project": {"_id": 0}}]
    docs = await db.aggregate(pipeline).to_list(length=days)
    # The DB will return ascending sorted from first date. If we want last `days`,
    # we sort descending by date, limit, then maybe sort ascending again.
    pipeline = [{"$sort": {"date": -1}}, {"$limit": days}, {"$project": {"_id": 0}}]
    docs = await db.aggregate(pipeline).to_list(length=days)
    return sorted(docs, key=lambda x: x["date"])


@router.get("/predictions", response_model=List[Prediction])
async def get_predictions(
    limit: int = Query(default=10, ge=1, le=50),
    risk_level: Optional[str] = Query(default=None)
):
    """Get AI-generated predictions"""
    db = await get_async_collection("predictions")
    query = {}
    if risk_level:
        query["risk_level"] = risk_level.lower()
    
    docs = await db.find(query).sort("prediction_date", -1).to_list(length=limit)
    return [doc_to_prediction(d) for d in docs]


@router.get("/alerts", response_model=List[Alert])
async def get_alerts(
    unread_only: bool = Query(default=False),
    limit: int = Query(default=10, ge=1, le=50)
):
    """Get active alerts"""
    db = await get_async_collection("alerts")
    query = {}
    if unread_only:
        query["is_read"] = False
        
    docs = await db.find(query).sort("created_at", -1).to_list(length=limit)
    return [doc_to_alert(d) for d in docs]


@router.post("/alerts/{alert_id}/read")
async def mark_alert_read(alert_id: str):
    """Mark an alert as read"""
    db = await get_async_collection("alerts")
    result = await db.update_one({"id": alert_id}, {"$set": {"is_read": True}})
    if result.modified_count > 0:
        return {"success": True, "message": "Alert marked as read"}
    return {"success": False, "message": "Alert not found"}


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Acknowledge an alert"""
    db = await get_async_collection("alerts")
    result = await db.update_one(
        {"id": alert_id}, 
        {"$set": {"is_acknowledged": True, "is_read": True}}
    )
    if result.modified_count > 0:
        return {"success": True, "message": "Alert acknowledged"}
    return {"success": False, "message": "Alert not found"}


@router.get("/suppliers", response_model=List[Supplier])
async def get_suppliers(
    limit: int = Query(default=15, ge=1, le=50),
    sort_by: str = Query(default="risk_score", description="Sort field: risk_score, name, tier")
):
    """Get supplier list with risk assessments"""
    db = await get_async_collection("suppliers")
    
    # Map sort_by parameter to valid MongoDB field
    sort_field = "risk_score"
    sort_dir = -1  # Descending for risk_score
    
    if sort_by == "name":
        sort_field = "name"
        sort_dir = 1
    elif sort_by == "tier":
        sort_field = "tier"
        sort_dir = 1
        
    docs = await db.find().sort(sort_field, sort_dir).to_list(length=limit)
    return [doc_to_supplier(d) for d in docs]


@router.get("/news", response_model=List[NewsArticle])
async def get_news(
    limit: int = Query(default=20, ge=1, le=50),
    region: Optional[str] = Query(default=None)
):
    """Get latest supply chain news with analysis"""
    db = await get_async_collection("news_articles")
    
    filter_query = {}
    if region:
        # Regex for case-insensitive partial match
        filter_query["region"] = {"$regex": region, "$options": "i"}
        
    docs = await db.find(filter_query).sort("published_at", -1).to_list(length=limit)
    return [doc_to_news(d) for d in docs]


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
    from app.services.data_simulator import get_data_store
    
    # Can still run synchronously since refresh_data is synchronous and will update DB
    data_store = get_data_store()
    data_store.refresh_data()
    return {
        "success": True, 
        "message": "Data refreshed",
        "timestamp": datetime.utcnow().isoformat()
    }
