"""
API Routes for Predictions and Risk Analysis
"""
from fastapi import APIRouter, Query, Body
from typing import List, Dict, Any
from datetime import datetime

from app.ml import get_risk_predictor
from app.nlp import get_nlp_pipeline
from app.services import get_data_store

router = APIRouter(prefix="/api/predictions", tags=["Predictions"])


@router.get("/forecast")
async def get_forecast(
    days: int = Query(default=30, ge=7, le=90, description="Days to forecast")
):
    """Get AI-generated risk forecast for future dates"""
    predictor = get_risk_predictor()
    forecast = predictor.predict_future_risk(days)
    return {
        "forecast": forecast,
        "generated_at": datetime.utcnow().isoformat(),
        "model_version": "1.0.0"
    }


@router.post("/analyze-text")
async def analyze_text(
    text: str = Body(..., embed=True, description="Text to analyze for supply chain risks")
):
    """Analyze text for supply chain risk indicators using NLP"""
    nlp = get_nlp_pipeline()
    result = nlp.analyze(text)
    
    return {
        "text": result.text[:200] + "..." if len(result.text) > 200 else result.text,
        "sentiment": {
            "score": result.sentiment_score,
            "category": result.sentiment_category.value
        },
        "entities": result.entities,
        "keywords": result.keywords,
        "disruption_type": result.disruption_type,
        "risk_indicators": result.risk_indicators,
        "confidence": result.confidence
    }


@router.get("/risk-assessment")
async def get_risk_assessment():
    """Get comprehensive risk assessment from all data sources"""
    predictor = get_risk_predictor()
    data_store = get_data_store()
    
    # Analyze news
    news_data = [
        {"sentiment_score": n.sentiment_score, "disruption_type": n.disruption_type.value if n.disruption_type else None}
        for n in data_store.news
    ]
    news_signal = predictor.analyze_news_risk(news_data)
    
    # Analyze suppliers
    supplier_data = [
        {"region": s.region, "tier": s.tier, "is_critical": s.is_critical}
        for s in data_store.suppliers
    ]
    supplier_signal = predictor.analyze_supplier_risk(supplier_data)
    
    # Historical pattern (for top region)
    top_region = data_store.region_risks[0] if data_store.region_risks else None
    historical_signal = predictor.analyze_historical_pattern(
        region=top_region.region_name if top_region else "Asia Pacific",
        disruption_type="geopolitical"
    )
    
    # Aggregate all signals
    aggregated = predictor.aggregate_signals([news_signal, supplier_signal, historical_signal])
    
    # Generate recommendations
    recommendations = predictor.generate_recommendations(aggregated)
    
    return {
        "overall_risk": {
            "score": aggregated.overall_score,
            "level": aggregated.risk_level.value,
            "confidence": aggregated.confidence,
            "trend": aggregated.trend
        },
        "contributing_factors": aggregated.top_factors,
        "recommendations": recommendations,
        "signals": [
            {
                "source": s.source,
                "risk_score": s.risk_score,
                "confidence": s.confidence,
                "factors": s.factors
            }
            for s in aggregated.contributing_signals
        ],
        "assessed_at": datetime.utcnow().isoformat()
    }


@router.get("/disruption-types")
async def get_disruption_type_analysis():
    """Get risk breakdown by disruption type"""
    data_store = get_data_store()
    
    # Analyze predictions by disruption type
    type_analysis = {}
    for pred in data_store.predictions:
        d_type = pred.disruption_type.value
        if d_type not in type_analysis:
            type_analysis[d_type] = {
                "count": 0,
                "avg_risk": 0,
                "total_risk": 0,
                "regions": set()
            }
        type_analysis[d_type]["count"] += 1
        type_analysis[d_type]["total_risk"] += pred.risk_score
        type_analysis[d_type]["regions"].add(pred.region)
    
    # Calculate averages
    result = []
    for d_type, data in type_analysis.items():
        result.append({
            "type": d_type,
            "display_name": d_type.replace("_", " ").title(),
            "prediction_count": data["count"],
            "average_risk": round(data["total_risk"] / data["count"], 3) if data["count"] > 0 else 0,
            "affected_regions": list(data["regions"])
        })
    
    return sorted(result, key=lambda x: x["average_risk"], reverse=True)


@router.get("/regional-breakdown")
async def get_regional_breakdown():
    """Get detailed risk breakdown by region"""
    data_store = get_data_store()
    
    return {
        "regions": [
            {
                "code": r.region_code,
                "name": r.region_name,
                "coordinates": {"lat": r.lat, "lng": r.lng},
                "risk_score": r.risk_score,
                "risk_level": r.risk_level.value,
                "active_alerts": r.active_alerts,
                "top_risks": r.top_risks
            }
            for r in data_store.region_risks
        ],
        "highest_risk_region": max(data_store.region_risks, key=lambda x: x.risk_score).region_name if data_store.region_risks else None
    }
