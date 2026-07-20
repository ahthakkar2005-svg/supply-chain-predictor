"""
API Routes for Dashboard Data with automatic DataStore fallback
"""
import logging
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
from app.services.data_simulator import get_data_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary():
    try:
        db = await get_async_collection("dashboard_summary")
        if db is not None:
            doc = await db.find_one()
            if doc:
                return doc_to_dashboard_summary(doc)
    except Exception as e:
        logger.warning(f"MongoDB summary fetch failed: {e}")
    
    return get_data_store().dashboard_summary


@router.get("/regions", response_model=List[RegionRisk])
async def get_region_risks():
    """Get risk data for all geographic regions"""
    try:
        db = await get_async_collection("region_risks")
        if db is not None:
            docs = await db.find().to_list(length=100)
            if docs:
                return [doc_to_region_risk(d) for d in docs]
    except Exception as e:
        logger.warning(f"MongoDB regions fetch failed: {e}")
    
    return get_data_store().region_risks


@router.get("/metrics", response_model=List[RiskMetric])
async def get_risk_metrics():
    """Get risk metrics by supply chain category"""
    try:
        db = await get_async_collection("risk_metrics")
        if db is not None:
            docs = await db.find().to_list(length=100)
            if docs:
                return [doc_to_risk_metric(d) for d in docs]
    except Exception as e:
        logger.warning(f"MongoDB metrics fetch failed: {e}")
    
    return get_data_store().risk_metrics


@router.get("/time-series")
async def get_time_series_data(
    days: int = Query(default=30, ge=7, le=90, description="Number of days of historical data")
):
    """Get time series data for trend charts"""
    try:
        db = await get_async_collection("time_series")
        if db is not None:
            pipeline = [{"$sort": {"date": -1}}, {"$limit": days}, {"$project": {"_id": 0}}]
            docs = await db.aggregate(pipeline).to_list(length=days)
            if docs:
                return sorted(docs, key=lambda x: x["date"])
    except Exception as e:
        logger.warning(f"MongoDB time-series fetch failed: {e}")
    
    return get_data_store().time_series[:days]


@router.get("/predictions", response_model=List[Prediction])
async def get_predictions(
    limit: int = Query(default=10, ge=1, le=50),
    risk_level: Optional[str] = Query(default=None)
):
    """Get AI-generated predictions"""
    try:
        db = await get_async_collection("predictions")
        if db is not None:
            query = {}
            if risk_level:
                query["risk_level"] = risk_level.lower()
            docs = await db.find(query).sort("prediction_date", -1).to_list(length=limit)
            if docs:
                return [doc_to_prediction(d) for d in docs]
    except Exception as e:
        logger.warning(f"MongoDB predictions fetch failed: {e}")
    
    preds = get_data_store().predictions
    if risk_level:
        preds = [p for p in preds if p.risk_level.value.lower() == risk_level.lower()]
    return preds[:limit]


@router.get("/alerts", response_model=List[Alert])
async def get_alerts(
    unread_only: bool = Query(default=False),
    limit: int = Query(default=10, ge=1, le=50)
):
    """Get active alerts"""
    try:
        db = await get_async_collection("alerts")
        if db is not None:
            query = {}
            if unread_only:
                query["is_read"] = False
            docs = await db.find(query).sort("created_at", -1).to_list(length=limit)
            if docs:
                return [doc_to_alert(d) for d in docs]
    except Exception as e:
        logger.warning(f"MongoDB alerts fetch failed: {e}")
    
    alerts = get_data_store().alerts
    if unread_only:
        alerts = [a for a in alerts if not a.is_read]
    return alerts[:limit]


@router.post("/alerts/{alert_id}/read")
async def mark_alert_read(alert_id: str):
    """Mark an alert as read"""
    try:
        db = await get_async_collection("alerts")
        if db is not None:
            result = await db.update_one({"id": alert_id}, {"$set": {"is_read": True}})
            if result.modified_count > 0:
                return {"success": True, "message": "Alert marked as read"}
    except Exception as e:
        logger.warning(f"MongoDB mark alert read failed: {e}")
    
    for alert in get_data_store().alerts:
        if alert.id == alert_id:
            alert.is_read = True
            return {"success": True, "message": "Alert marked as read"}
    return {"success": False, "message": "Alert not found"}


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Acknowledge an alert"""
    try:
        db = await get_async_collection("alerts")
        if db is not None:
            result = await db.update_one(
                {"id": alert_id}, 
                {"$set": {"is_acknowledged": True, "is_read": True}}
            )
            if result.modified_count > 0:
                return {"success": True, "message": "Alert acknowledged"}
    except Exception as e:
        logger.warning(f"MongoDB acknowledge alert failed: {e}")
    
    for alert in get_data_store().alerts:
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
    try:
        db = await get_async_collection("suppliers")
        if db is not None:
            sort_field = "risk_score"
            sort_dir = -1
            if sort_by == "name":
                sort_field = "name"
                sort_dir = 1
            elif sort_by == "tier":
                sort_field = "tier"
                sort_dir = 1
            docs = await db.find().sort(sort_field, sort_dir).to_list(length=limit)
            if docs:
                return [doc_to_supplier(d) for d in docs]
    except Exception as e:
        logger.warning(f"MongoDB suppliers fetch failed: {e}")
    
    suppliers = get_data_store().suppliers
    if sort_by == "name":
        suppliers = sorted(suppliers, key=lambda s: s.name)
    elif sort_by == "tier":
        suppliers = sorted(suppliers, key=lambda s: s.tier)
    else:
        suppliers = sorted(suppliers, key=lambda s: s.risk_score, reverse=True)
    return suppliers[:limit]


@router.get("/news", response_model=List[NewsArticle])
async def get_news(
    limit: int = Query(default=20, ge=1, le=50),
    region: Optional[str] = Query(default=None)
):
    """Get latest supply chain news with analysis"""
    try:
        db = await get_async_collection("news_articles")
        if db is not None:
            filter_query = {}
            if region:
                filter_query["region"] = {"$regex": region, "$options": "i"}
            docs = await db.find(filter_query).sort("published_at", -1).to_list(length=limit)
            if docs:
                return [doc_to_news(d) for d in docs]
    except Exception as e:
        logger.warning(f"MongoDB news fetch failed: {e}")
    
    news = get_data_store().news
    if region:
        news = [n for n in news if region.lower() in (n.region or "").lower()]
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

    if region:
        ports = [p for p in ports if region.lower() in p["region"].lower()]

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
