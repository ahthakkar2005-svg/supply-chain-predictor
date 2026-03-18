"""
Alert Service — FIX 5 / FIX 11
Manages alert lifecycle: creation, acknowledgement with ownership, audit logging.
"""
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from app.models import Alert, RiskLevel, DisruptionType

logger = logging.getLogger(__name__)


class AlertService:
    """
    CRUD + business logic for alerts.
    Writes audit log entries on every acknowledgement (FIX 11).
    """

    def __init__(self):
        pass

    async def create_alert(
        self,
        title: str,
        message: str,
        risk_level: RiskLevel,
        disruption_type: DisruptionType,
        region: str,
        tenant_id: str = "default",
    ) -> Alert:
        """Create a new alert and persist to MongoDB."""
        alert = Alert(
            id=str(uuid.uuid4()),
            created_at=datetime.utcnow(),
            title=title,
            message=message,
            risk_level=risk_level,
            disruption_type=disruption_type,
            region=region,
            is_read=False,
            is_acknowledged=False,
        )

        from app.core.database import get_async_collection
        db_alerts = await get_async_collection("alerts")
        doc = alert.model_dump()
        doc["_id"] = doc.pop("id")
        doc["risk_level"] = doc["risk_level"].value if hasattr(doc["risk_level"], "value") else doc["risk_level"]
        doc["disruption_type"] = doc["disruption_type"].value if hasattr(doc["disruption_type"], "value") else doc["disruption_type"]
        doc["tenant_id"] = tenant_id
        await db_alerts.insert_one(doc)
        logger.info(f"Alert created: {title} [{risk_level.value}]")

        return alert

    async def acknowledge_alert(
        self,
        alert_id: str,
        user_id: str,
        user_email: str,
        tenant_id: str,
    ) -> Dict:
        """
        Acknowledge an alert and write audit log.
        FIX 11: Records who acknowledged and when.
        """
        from app.core.database import get_async_collection
        db_alerts = await get_async_collection("alerts")
        db_audit = await get_async_collection("audit_logs")

        now = datetime.utcnow()
        result = await db_alerts.update_one(
            {"_id": alert_id, "tenant_id": tenant_id},
            {
                "$set": {
                    "is_acknowledged": True,
                    "is_read": True,
                    "acknowledged_by": user_id,
                    "acknowledged_at": now,
                }
            },
        )

        if result.modified_count == 0:
            return {"success": False, "message": "Alert not found or unauthorized"}

        # Write audit log entry (FIX 11)
        await db_audit.insert_one({
            "_id": str(uuid.uuid4()),
            "user_id": user_id,
            "user_email": user_email,
            "tenant_id": tenant_id,
            "action": "alert.acknowledge",
            "resource_type": "alert",
            "resource_id": alert_id,
            "timestamp": now,
            "result": "success",
            "ip_address": None,  # Set by middleware
        })

        logger.info(f"Alert {alert_id} acknowledged by {user_email}")
        return {"success": True, "message": "Alert acknowledged", "acknowledged_at": now.isoformat()}

    async def mark_read(self, alert_id: str, tenant_id: str) -> Dict:
        """Mark an alert as read."""
        from app.core.database import get_async_collection
        db_alerts = await get_async_collection("alerts")

        result = await db_alerts.update_one(
            {"_id": alert_id, "tenant_id": tenant_id},
            {"$set": {"is_read": True}},
        )
        if result.modified_count == 0:
            return {"success": False, "message": "Alert not found"}
        return {"success": True, "message": "Alert marked as read"}

    async def get_alerts(
        self,
        tenant_id: str,
        unread_only: bool = False,
        limit: int = 50,
    ) -> List[Dict]:
        """Get alerts for a tenant."""
        from app.core.database import get_async_collection
        db_alerts = await get_async_collection("alerts")

        query: Dict = {"tenant_id": tenant_id}
        if unread_only:
            query["is_read"] = False

        cursor = db_alerts.find(query).sort("created_at", -1).limit(limit)
        results = []
        async for doc in cursor:
            doc["id"] = doc.pop("_id")
            results.append(doc)
        return results
