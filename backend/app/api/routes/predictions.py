"""
API Routes for Predictions and Risk Analysis
"""
from fastapi import APIRouter, Query, Body
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.ml import get_risk_predictor
from app.nlp import get_nlp_pipeline
from app.core.database import get_async_collection
from app.models.db_models import doc_to_news, doc_to_supplier, doc_to_region_risk, doc_to_prediction
from app.models.schemas import ScenarioInput, RouteAnalysisRequest, RouteAnalysisResponse
from app.ml.predictor import AggregatedRisk
from app.services.route_calculator import RouteCalculator

router = APIRouter(prefix="/api/predictions", tags=["Predictions"])


@router.get("/forecast")
async def get_forecast(
    days: int = Query(default=30, ge=7, le=90, description="Days to forecast"),
    region: Optional[str] = Query(default=None, description="Filter forecast for a specific region")
):
    """Get AI-generated risk forecast for future dates"""
    predictor = get_risk_predictor()
    forecast = predictor.predict_future_risk(days, region=region)
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
    
    # Analyze news
    db_news = await get_async_collection("news_articles")
    news_docs = await db_news.find().sort("published_at", -1).limit(50).to_list(length=50)
    news_data = [
        {"sentiment_score": doc_to_news(n).sentiment_score, "disruption_type": doc_to_news(n).disruption_type.value if doc_to_news(n).disruption_type else None}
        for n in news_docs
    ]
    news_signal = predictor.analyze_news_risk(news_data)
    
    # Analyze suppliers
    db_suppliers = await get_async_collection("suppliers")
    supplier_docs = await db_suppliers.find().to_list(length=50)
    supplier_data = [
        {"region": doc_to_supplier(s).region, "tier": doc_to_supplier(s).tier, "is_critical": doc_to_supplier(s).is_critical}
        for s in supplier_docs
    ]
    supplier_signal = predictor.analyze_supplier_risk(supplier_data)
    
    # Historical pattern (for top region)
    db_regions = await get_async_collection("region_risks")
    region_docs = await db_regions.find().sort("risk_score", -1).limit(1).to_list(length=1)
    
    top_region = doc_to_region_risk(region_docs[0]) if region_docs else None
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
    db_preds = await get_async_collection("predictions")
    pred_docs = await db_preds.find().to_list(length=100)
    predictions = [doc_to_prediction(d) for d in pred_docs]
    
    # Analyze predictions by disruption type
    type_analysis = {}
    for pred in predictions:
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
    db_regions = await get_async_collection("region_risks")
    region_docs = await db_regions.find().to_list(length=100)
    region_risks = [doc_to_region_risk(d) for d in region_docs]
    
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
            for r in region_risks
        ],
        "highest_risk_region": max(region_risks, key=lambda x: x.risk_score).region_name if region_risks else None
    }


@router.post("/scenario")
async def simulate_scenario(
    scenario: ScenarioInput = Body(..., description="Hypothetical risk factors for simulation")
):
    """Test custom 'What-If' scenarios to simulate risk impact"""
    predictor = get_risk_predictor()
    
    # Predict point-in-time score using XGBoost
    features = scenario.dict()
    prediction = predictor.predict_risk_score(features)
    
    # Map raw float score to a RiskLevel Enum
    risk_level_enum = predictor._get_risk_level(prediction["risk_score"])
    
    # Mock an AggregatedRisk object to use the existing recommendation engine
    dummy_risk = AggregatedRisk(
        overall_score=prediction["risk_score"],
        risk_level=risk_level_enum,
        confidence=prediction.get("confidence", 0.8),
        contributing_signals=[],
        top_factors=["Custom simulation parameters triggered outcome"],
        trend="stable"
    )
    
    recommendations = predictor.generate_recommendations(dummy_risk)
    
    # Attach generated metadata
    prediction.update({
        "risk_level": risk_level_enum.value,
        "recommendations": recommendations,
        "simulated": True,
        "generated_at": datetime.utcnow().isoformat()
    })
    
    return prediction


@router.post("/route-analysis", response_model=RouteAnalysisResponse)
async def analyze_shipping_route(
    request: RouteAnalysisRequest = Body(..., description="Shipping route details for analysis")
):
    """Analyze a shipping route for ETAs, costs, and potential live disruptions"""
    try:
        response = RouteCalculator.analyze_route(request)
        return response
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(e))
