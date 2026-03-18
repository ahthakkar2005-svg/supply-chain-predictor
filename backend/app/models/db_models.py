"""
MongoDB Document Converters
Utility functions to convert between Pydantic models and MongoDB documents
"""
import json
from datetime import datetime


def pydantic_to_doc(obj) -> dict:
    """Convert a Pydantic model to a MongoDB-friendly dict"""
    data = obj.model_dump() if hasattr(obj, "model_dump") else obj.dict()
    # Convert enums to their values
    for key, value in data.items():
        if hasattr(value, "value"):
            data[key] = value.value
    # Use Pydantic 'id' as MongoDB '_id'
    if "id" in data:
        data["_id"] = data.pop("id")
    return data


def doc_to_news(doc: dict):
    """Convert MongoDB document to NewsArticle"""
    from app.models import NewsArticle, DisruptionType
    doc["id"] = str(doc.pop("_id", doc.get("id", "")))
    if doc.get("disruption_type"):
        doc["disruption_type"] = DisruptionType(doc["disruption_type"])
    return NewsArticle(**doc)


def doc_to_prediction(doc: dict):
    """Convert MongoDB document to Prediction"""
    from app.models import Prediction, RiskLevel, DisruptionType
    doc["id"] = str(doc.pop("_id", doc.get("id", "")))
    doc["risk_level"] = RiskLevel(doc["risk_level"])
    doc["disruption_type"] = DisruptionType(doc["disruption_type"])
    return Prediction(**doc)


def doc_to_alert(doc: dict):
    """Convert MongoDB document to Alert"""
    from app.models import Alert, RiskLevel, DisruptionType
    doc["id"] = str(doc.pop("_id", doc.get("id", "")))
    doc["risk_level"] = RiskLevel(doc["risk_level"])
    doc["disruption_type"] = DisruptionType(doc["disruption_type"])
    return Alert(**doc)


def doc_to_supplier(doc: dict):
    """Convert MongoDB document to Supplier"""
    from app.models import Supplier
    doc["id"] = str(doc.pop("_id", doc.get("id", "")))
    return Supplier(**doc)


def doc_to_region_risk(doc: dict):
    """Convert MongoDB document to RegionRisk"""
    from app.models import RegionRisk, RiskLevel
    doc.pop("_id", None)
    doc["risk_level"] = RiskLevel(doc["risk_level"])
    return RegionRisk(**doc)


def doc_to_risk_metric(doc: dict):
    """Convert MongoDB document to RiskMetric"""
    from app.models import RiskMetric
    doc.pop("_id", None)
    return RiskMetric(**doc)


def doc_to_dashboard_summary(doc: dict):
    """Convert MongoDB document to DashboardSummary"""
    from app.models import DashboardSummary, RiskLevel
    doc.pop("_id", None)
    doc["overall_risk_level"] = RiskLevel(doc["overall_risk_level"])
    return DashboardSummary(**doc)
