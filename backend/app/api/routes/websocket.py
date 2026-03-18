"""
WebSocket Route - Real-time data streaming endpoint
"""
import logging
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.connection_manager import get_connection_manager
from app.services.news_service import get_news_service
from app.services.weather_service import get_weather_service
from app.core.database import get_async_collection
from app.models.db_models import (
    doc_to_dashboard_summary, doc_to_region_risk, doc_to_alert,
    doc_to_news, doc_to_risk_metric, doc_to_supplier
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates.
    
    On connect: sends full state snapshot.
    Then keeps connection open for push updates from the RealtimeEngine.
    """
    manager = get_connection_manager()
    await manager.connect(websocket)

    try:
        # Send initial state snapshot
        await _send_initial_snapshot(websocket)

        # Keep connection alive and listen for client messages
        while True:
            try:
                # Wait for client messages (ping/pong or commands)
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle client commands
                if message.get("type") == "ping":
                    await websocket.send_json({"event": "pong"})
                elif message.get("type") == "refresh":
                    await _send_initial_snapshot(websocket)

            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected from WebSocket")
    except Exception as e:
        manager.disconnect(websocket)
        logger.error(f"WebSocket error: {e}")


async def _send_initial_snapshot(websocket: WebSocket):
    """Send full current state to a newly connected client"""
    news_service = get_news_service()
    weather_service = get_weather_service()

    # Load from MongoDB
    db_summary = await get_async_collection("dashboard_summary")
    summary_doc = await db_summary.find_one()
    summary = doc_to_dashboard_summary(summary_doc) if summary_doc else None

    db_regions = await get_async_collection("region_risks")
    region_docs = await db_regions.find().to_list(length=100)
    region_risks = [doc_to_region_risk(d) for d in region_docs]

    db_alerts = await get_async_collection("alerts")
    alert_docs = await db_alerts.find().to_list(length=100)
    alerts = [doc_to_alert(d) for d in alert_docs]

    db_news = await get_async_collection("news_articles")
    news_docs = await db_news.find().sort("published_at", -1).limit(20).to_list(length=20)
    news_articles = [doc_to_news(d) for d in news_docs]

    db_metrics = await get_async_collection("risk_metrics")
    metric_docs = await db_metrics.find().to_list(length=100)
    metrics = [doc_to_risk_metric(d) for d in metric_docs]

    db_suppliers = await get_async_collection("suppliers")
    supplier_docs = await db_suppliers.find().to_list(length=100)
    suppliers = [doc_to_supplier(d) for d in supplier_docs]

    snapshot = {
        "event": "initial_snapshot",
        "data": {
            "summary": {
                "overall_risk_score": summary.overall_risk_score,
                "overall_risk_level": summary.overall_risk_level.value,
                "risk_trend": summary.risk_trend,
                "total_active_alerts": summary.total_active_alerts,
                "critical_alerts": summary.critical_alerts,
                "high_alerts": summary.high_alerts,
                "regions_at_risk": summary.regions_at_risk,
                "predictions_accuracy": summary.predictions_accuracy,
                "last_updated": summary.last_updated.isoformat(),
            } if summary else {},
            "regions": [
                {
                    "region_code": r.region_code,
                    "region_name": r.region_name,
                    "lat": r.lat,
                    "lng": r.lng,
                    "risk_score": r.risk_score,
                    "risk_level": r.risk_level.value,
                    "active_alerts": r.active_alerts,
                    "top_risks": r.top_risks,
                }
                for r in region_risks
            ],
            "alerts": [
                {
                    "id": a.id,
                    "title": a.title,
                    "message": a.message,
                    "risk_level": a.risk_level.value,
                    "region": a.region,
                    "is_read": a.is_read,
                    "created_at": a.created_at.isoformat(),
                }
                for a in alerts
            ],
            "news": [
                {
                    "id": n.id,
                    "title": n.title,
                    "source": n.source,
                    "sentiment_score": n.sentiment_score,
                    "published_at": n.published_at.isoformat(),
                    "region": n.region,
                }
                for n in news_articles
            ],
            "metrics": [
                {
                    "category": m.category,
                    "current_score": m.current_score,
                    "previous_score": m.previous_score,
                    "trend": m.trend,
                    "change_percent": m.change_percent,
                }
                for m in metrics
            ],
            "suppliers": [
                {
                    "id": s.id,
                    "name": s.name,
                    "region": s.region,
                    "risk_score": s.risk_score,
                    "tier": s.tier,
                    "is_critical": s.is_critical,
                }
                for s in suppliers
            ],
            "weather_conditions": weather_service.get_current_conditions(),
            "api_status": {
                "news_api": news_service.is_configured,
                "weather_api": weather_service.is_configured,
            },
        },
    }

    await websocket.send_json(snapshot)
    logger.info("Sent initial snapshot to client")
