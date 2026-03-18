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
from app.core.database import get_async_collection
from app.models.db_models import (
    doc_to_dashboard_summary, doc_to_region_risk, doc_to_alert,
    doc_to_news, doc_to_risk_metric, doc_to_supplier
)
from app.models import RiskLevel
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

                # Fetch real news
                articles = await news_service.fetch_news(20)

                if articles:
                    db_news = await get_async_collection("news_articles")
                    
                    # Deduplicate and sort
                    new_articles = []
                    # In a real app we'd query by URL or dedup hash, here we do a simple check
                    # Or batch insert with unordered=True
                    
                    for article in articles:
                        # Convert model to doc
                        doc = {
                            "id": article.id,
                            "title": article.title,
                            "source": article.source,
                            "sentiment_score": article.sentiment_score,
                            "published_at": article.published_at,
                            "region": article.region,
                            "disruption_type": article.disruption_type.value if article.disruption_type else None
                        }
                        # Simple upsert by title to avoid dupes purely for demo
                        result = await db_news.update_one(
                            {"title": article.title}, 
                            {"$setOnInsert": doc},
                            upsert=True
                        )
                        if result.upserted_id:
                            new_articles.append(article)

                    # Broadcast new articles
                    if new_articles and manager.connection_count > 0:
                        total_count = await db_news.count_documents({})
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
                                for a in new_articles[:5]
                            ],
                            "total_count": total_count,
                        })
                        logger.info(f"📰 Broadcast {len(new_articles)} new articles")

                # Update the dashboard summary timestamp
                db_summary = await get_async_collection("dashboard_summary")
                await db_summary.update_many({}, {"$set": {"last_updated": datetime.utcnow()}})

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

                # Fetch weather alerts
                weather_alerts = await weather_service.fetch_weather_alerts()

                if weather_alerts:
                    db_alerts = await get_async_collection("alerts")
                    for alert in weather_alerts:
                        doc = {
                            "id": alert.id,
                            "title": alert.title,
                            "message": alert.message,
                            "risk_level": alert.risk_level.value,
                            "region": alert.region,
                            "created_at": alert.created_at,
                            "is_read": alert.is_read,
                            "is_acknowledged": alert.is_acknowledged
                        }
                        await db_alerts.update_one({"id": alert.id}, {"$setOnInsert": doc}, upsert=True)

                    total_alerts = await db_alerts.count_documents({})
                    critical_alerts = await db_alerts.count_documents({"risk_level": "critical"})

                    # Update summary
                    db_summary = await get_async_collection("dashboard_summary")
                    await db_summary.update_many(
                        {},
                        {"$set": {
                            "total_active_alerts": total_alerts,
                            "critical_alerts": critical_alerts
                        }}
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
        db_summary = await get_async_collection("dashboard_summary")
        doc = await db_summary.find_one()
        if not doc:
            return
            
        summary = doc_to_dashboard_summary(doc)

        # Small random drift to risk score (±0.02)
        drift = random.gauss(0, 0.01)
        new_score = float(max(0.05, min(0.98, float(summary.overall_risk_score) + drift)))
        old_score = float(summary.overall_risk_score)
        final_score = float(round(new_score, 3))

        # Update risk trend
        trend = "stable"
        if final_score > old_score + 0.01:
            trend = "up"
        elif final_score < old_score - 0.01:
            trend = "down"

        # Update risk level
        risk_level = RiskLevel.LOW
        if final_score >= 0.85:
            risk_level = RiskLevel.CRITICAL
        elif final_score >= 0.7:
            risk_level = RiskLevel.HIGH
        elif final_score >= 0.4:
            risk_level = RiskLevel.MEDIUM

        now = datetime.utcnow()
        await db_summary.update_one(
            {"_id": doc["_id"]},
            {"$set": {
                "overall_risk_score": final_score,
                "risk_trend": trend,
                "overall_risk_level": risk_level.value,
                "last_updated": now
            }}
        )

        await manager.broadcast("risk_update", {
            "overall_risk_score": final_score,
            "overall_risk_level": risk_level.value,
            "risk_trend": trend,
            "total_active_alerts": summary.total_active_alerts,
            "critical_alerts": summary.critical_alerts,
            "high_alerts": summary.high_alerts,
            "last_updated": now.isoformat(),
        })

    async def _broadcast_metrics_update(self):
        """Update category metrics with small drift"""
        manager = get_connection_manager()
        db_metrics = await get_async_collection("risk_metrics")
        
        docs = await db_metrics.find().to_list(length=100)
        updated_metrics = []

        for doc in docs:
            metric_doc = doc_to_risk_metric(doc)
            drift = random.gauss(0, 0.015)
            old_score = float(metric_doc.current_score)
            new_score = float(max(0.05, min(0.95, float(metric_doc.current_score) + drift)))
            
            # calculate changes
            new_cur = float(round(new_score, 3))
            change = new_cur - old_score
            
            trend = "stable"
            if abs(change) >= 0.01:
                trend = "up" if change > 0 else "down"

            change_pct = float(round(float(change) * 100.0, 1))

            # Update DB
            await db_metrics.update_one(
                {"_id": doc["_id"]},
                {"$set": {
                    "previous_score": old_score,
                    "current_score": new_cur,
                    "trend": trend,
                    "change_percent": change_pct
                }}
            )

            updated_metrics.append({
                "category": metric_doc.category,
                "current_score": new_cur,
                "previous_score": old_score,
                "trend": trend,
                "change_percent": change_pct,
            })

        await manager.broadcast("metrics_update", {
            "metrics": updated_metrics
        })

    async def _broadcast_region_update(self):
        """Update region risks with drift"""
        manager = get_connection_manager()
        db_regions = await get_async_collection("region_risks")
        docs = await db_regions.find().to_list(length=100)

        updated_regions = []

        for doc in docs:
            region = doc_to_region_risk(doc)
            drift = random.gauss(0, 0.02)
            new_score = float(max(0.05, min(0.95, float(region.risk_score) + drift)))
            final_score = float(round(new_score, 3))

            risk_level = RiskLevel.LOW
            if final_score >= 0.85:
                risk_level = RiskLevel.CRITICAL
            elif final_score >= 0.7:
                risk_level = RiskLevel.HIGH
            elif final_score >= 0.4:
                risk_level = RiskLevel.MEDIUM

            # Update DB
            await db_regions.update_one(
                {"_id": doc["_id"]},
                {"$set": {
                    "risk_score": final_score,
                    "risk_level": risk_level.value
                }}
            )

            updated_regions.append({
                "region_code": region.region_code,
                "region_name": region.region_name,
                "lat": region.lat,
                "lng": region.lng,
                "risk_score": final_score,
                "risk_level": risk_level.value,
                "active_alerts": region.active_alerts,
                "top_risks": region.top_risks,
            })

        await manager.broadcast("region_update", {
            "regions": updated_regions
        })


# Singleton
_engine: Optional[RealtimeEngine] = None


def get_realtime_engine() -> RealtimeEngine:
    global _engine
    if _engine is None:
        _engine = RealtimeEngine()
    return _engine
