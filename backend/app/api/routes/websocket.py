"""
WebSocket Route - Real-time data streaming endpoint
"""
import logging
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.connection_manager import get_connection_manager
from app.services.data_simulator import get_data_store
from app.services.news_service import get_news_service
from app.services.weather_service import get_weather_service

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
    data_store = get_data_store()
    news_service = get_news_service()
    weather_service = get_weather_service()

    summary = data_store.dashboard_summary
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
            },
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
                for r in data_store.region_risks
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
                for a in data_store.alerts
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
                for n in data_store.news[:20]
            ],
            "metrics": [
                {
                    "category": m.category,
                    "current_score": m.current_score,
                    "previous_score": m.previous_score,
                    "trend": m.trend,
                    "change_percent": m.change_percent,
                }
                for m in data_store.risk_metrics
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
                for s in data_store.suppliers
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
