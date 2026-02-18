"""
Real-time Data Engine
Background task that fetches live data from external APIs and broadcasts updates via WebSocket
"""
import asyncio
import logging
import random
import math
from datetime import datetime
from typing import Optional

from app.services.connection_manager import get_connection_manager
from app.services.news_service import get_news_service
from app.services.weather_service import get_weather_service
from app.services.data_simulator import get_data_store
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class RealtimeEngine:
    """
    Background engine that:
    - Fetches real news from NewsAPI every 60 seconds
    - Fetches weather from OpenWeatherMap every 60 seconds
    - Applies incremental risk score drift every 5 seconds
    - Broadcasts all changes via WebSocket
    """

    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._news_task: Optional[asyncio.Task] = None
        self._weather_task: Optional[asyncio.Task] = None
        self._tick_count = 0

    async def start(self):
        """Start the real-time engine"""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._tick_loop())
        self._news_task = asyncio.create_task(self._news_loop())
        self._weather_task = asyncio.create_task(self._weather_loop())
        logger.info("🚀 Real-time engine started")

    async def stop(self):
        """Stop the real-time engine"""
        self._running = False
        for task in [self._task, self._news_task, self._weather_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        logger.info("🛑 Real-time engine stopped")

    async def _tick_loop(self):
        """Main tick loop - applies risk drift every 5 seconds"""
        while self._running:
            try:
                await asyncio.sleep(5)
                self._tick_count += 1

                manager = get_connection_manager()
                if manager.connection_count == 0:
                    continue

                # Apply incremental risk score changes
                await self._broadcast_risk_update()

                # Every 3rd tick (~15 seconds), update metrics
                if self._tick_count % 3 == 0:
                    await self._broadcast_metrics_update()

                # Every 6th tick (~30 seconds), update regions
                if self._tick_count % 6 == 0:
                    await self._broadcast_region_update()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Tick loop error: {e}")
                await asyncio.sleep(5)

    async def _news_loop(self):
        """Fetch news from API every 60 seconds"""
        # Initial delay to let the app start
        await asyncio.sleep(3)

        while self._running:
            try:
                manager = get_connection_manager()
                news_service = get_news_service()
                data_store = get_data_store()

                # Fetch real news
                articles = await news_service.fetch_news(20)

                if articles:
                    # Update the data store
                    new_articles = []
                    existing_titles = {n.title for n in data_store.news}

                    for article in articles:
                        if article.title not in existing_titles:
                            new_articles.append(article)
                            data_store.news.insert(0, article)

                    # Keep only last 50 articles
                    data_store.news = data_store.news[:50]

                    # Broadcast new articles
                    if new_articles and manager.connection_count > 0:
                        await manager.broadcast("new_news", {
                            "articles": [
                                {
                                    "id": a.id,
                                    "title": a.title,
                                    "source": a.source,
                                    "sentiment_score": a.sentiment_score,
                                    "published_at": a.published_at.isoformat(),
                                    "region": a.region,
                                    "disruption_type": a.disruption_type.value if a.disruption_type else None,
                                }
                                for a in new_articles[:5]  # Max 5 new articles per broadcast
                            ],
                            "total_count": len(data_store.news),
                        })
                        logger.info(f"📰 Broadcast {len(new_articles)} new articles")

                # Also update the dashboard summary timestamp
                data_store.dashboard_summary.last_updated = datetime.utcnow()

                await asyncio.sleep(60)  # Fetch every 60 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"News loop error: {e}")
                await asyncio.sleep(60)

    async def _weather_loop(self):
        """Fetch weather alerts every 60 seconds"""
        # Stagger from news loop
        await asyncio.sleep(10)

        while self._running:
            try:
                manager = get_connection_manager()
                weather_service = get_weather_service()
                data_store = get_data_store()

                # Fetch weather alerts
                weather_alerts = await weather_service.fetch_weather_alerts()

                if weather_alerts:
                    for alert in weather_alerts:
                        data_store.alerts.insert(0, alert)

                    # Keep only last 20 alerts
                    data_store.alerts = data_store.alerts[:20]

                    # Update summary
                    data_store.dashboard_summary.total_active_alerts = len(data_store.alerts)
                    data_store.dashboard_summary.critical_alerts = len(
                        [a for a in data_store.alerts if a.risk_level.value == "critical"]
                    )

                    # Broadcast weather alerts
                    if manager.connection_count > 0:
                        await manager.broadcast("weather_alert", {
                            "alerts": [
                                {
                                    "id": a.id,
                                    "title": a.title,
                                    "message": a.message,
                                    "risk_level": a.risk_level.value,
                                    "region": a.region,
                                    "created_at": a.created_at.isoformat(),
                                }
                                for a in weather_alerts
                            ]
                        })
                        logger.info(f"🌦️ Broadcast {len(weather_alerts)} weather alerts")

                # Broadcast current conditions
                conditions = weather_service.get_current_conditions()
                if conditions and manager.connection_count > 0:
                    await manager.broadcast("weather_conditions", conditions)

                await asyncio.sleep(60)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Weather loop error: {e}")
                await asyncio.sleep(60)

    async def _broadcast_risk_update(self):
        """Apply small risk drift and broadcast"""
        manager = get_connection_manager()
        data_store = get_data_store()
        summary = data_store.dashboard_summary

        # Small random drift to risk score (±0.02)
        drift = random.gauss(0, 0.01)
        new_score = max(0.05, min(0.98, summary.overall_risk_score + drift))
        old_score = summary.overall_risk_score
        summary.overall_risk_score = round(new_score, 3)

        # Update risk trend
        if new_score > old_score + 0.01:
            summary.risk_trend = "up"
        elif new_score < old_score - 0.01:
            summary.risk_trend = "down"
        else:
            summary.risk_trend = "stable"

        summary.last_updated = datetime.utcnow()

        # Update risk level
        from app.models import RiskLevel
        if new_score >= 0.85:
            summary.overall_risk_level = RiskLevel.CRITICAL
        elif new_score >= 0.7:
            summary.overall_risk_level = RiskLevel.HIGH
        elif new_score >= 0.4:
            summary.overall_risk_level = RiskLevel.MEDIUM
        else:
            summary.overall_risk_level = RiskLevel.LOW

        await manager.broadcast("risk_update", {
            "overall_risk_score": summary.overall_risk_score,
            "overall_risk_level": summary.overall_risk_level.value,
            "risk_trend": summary.risk_trend,
            "total_active_alerts": summary.total_active_alerts,
            "critical_alerts": summary.critical_alerts,
            "high_alerts": summary.high_alerts,
            "last_updated": summary.last_updated.isoformat(),
        })

    async def _broadcast_metrics_update(self):
        """Update category metrics with small drift"""
        manager = get_connection_manager()
        data_store = get_data_store()

        for metric in data_store.risk_metrics:
            drift = random.gauss(0, 0.015)
            old_score = metric.current_score
            new_score = max(0.05, min(0.95, metric.current_score + drift))
            metric.previous_score = old_score
            metric.current_score = round(new_score, 3)

            change = new_score - old_score
            if abs(change) < 0.01:
                metric.trend = "stable"
            elif change > 0:
                metric.trend = "up"
            else:
                metric.trend = "down"
            metric.change_percent = round(change * 100, 1)

        await manager.broadcast("metrics_update", {
            "metrics": [
                {
                    "category": m.category,
                    "current_score": m.current_score,
                    "previous_score": m.previous_score,
                    "trend": m.trend,
                    "change_percent": m.change_percent,
                }
                for m in data_store.risk_metrics
            ]
        })

    async def _broadcast_region_update(self):
        """Update region risks with drift"""
        manager = get_connection_manager()
        data_store = get_data_store()

        from app.models import RiskLevel

        for region in data_store.region_risks:
            drift = random.gauss(0, 0.02)
            new_score = max(0.05, min(0.95, region.risk_score + drift))
            region.risk_score = round(new_score, 3)

            if new_score >= 0.85:
                region.risk_level = RiskLevel.CRITICAL
            elif new_score >= 0.7:
                region.risk_level = RiskLevel.HIGH
            elif new_score >= 0.4:
                region.risk_level = RiskLevel.MEDIUM
            else:
                region.risk_level = RiskLevel.LOW

        await manager.broadcast("region_update", {
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
            ]
        })


# Singleton
_engine: Optional[RealtimeEngine] = None


def get_realtime_engine() -> RealtimeEngine:
    global _engine
    if _engine is None:
        _engine = RealtimeEngine()
    return _engine
