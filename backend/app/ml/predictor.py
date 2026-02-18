"""
Risk Prediction Engine
Combines multiple signals to generate risk predictions
"""
import math
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from app.models import RiskLevel, DisruptionType, Prediction
from app.nlp import get_nlp_pipeline


@dataclass
class RiskSignal:
    """Individual risk signal from various sources"""
    source: str  # "news", "sentiment", "historical", "supplier"
    risk_score: float  # 0-1
    confidence: float  # 0-1
    disruption_type: Optional[str]
    region: Optional[str]
    factors: List[str]


@dataclass
class AggregatedRisk:
    """Aggregated risk from multiple signals"""
    overall_score: float
    risk_level: RiskLevel
    confidence: float
    contributing_signals: List[RiskSignal]
    top_factors: List[str]
    trend: str  # "increasing", "stable", "decreasing"


class RiskPredictor:
    """
    AI-powered risk prediction engine
    Combines NLP analysis, historical patterns, and multi-factor risk scoring
    """
    
    def __init__(self):
        self.nlp = get_nlp_pipeline()
        
        # Weights for different risk signals
        self.signal_weights = {
            "news_sentiment": 0.25,
            "news_volume": 0.15,
            "historical_pattern": 0.20,
            "supplier_concentration": 0.15,
            "geopolitical_index": 0.15,
            "market_volatility": 0.10,
        }
        
        # Regional risk modifiers
        self.regional_risk_base = {
            "Asia Pacific": 0.55,  # Higher due to concentration
            "Europe": 0.40,
            "North America": 0.35,
            "Latin America": 0.45,
            "Middle East & Africa": 0.50,
        }
        
        # Disruption type severity multipliers
        self.severity_multipliers = {
            "natural_disaster": 1.3,
            "geopolitical": 1.2,
            "economic": 1.0,
            "transportation": 0.9,
            "labor": 0.8,
            "cyber": 1.1,
            "supplier": 1.0,
        }
    
    def analyze_news_risk(self, news_items: List[Dict[str, Any]]) -> RiskSignal:
        """Analyze risk from news sentiment and volume"""
        if not news_items:
            return RiskSignal(
                source="news_sentiment",
                risk_score=0.3,  # Baseline uncertainty
                confidence=0.5,
                disruption_type=None,
                region=None,
                factors=["No recent news data"]
            )
        
        # Aggregate sentiment
        sentiments = [item.get("sentiment_score", 0) for item in news_items]
        avg_sentiment = sum(sentiments) / len(sentiments)
        
        # Convert sentiment to risk (negative = higher risk)
        risk_score = 0.5 - (avg_sentiment * 0.5)
        risk_score = max(0, min(1, risk_score))
        
        # Volume indicator
        volume_factor = min(len(news_items) / 20, 1.0) * 0.1
        risk_score += volume_factor
        
        # Identify dominant disruption type
        disruption_counts = {}
        for item in news_items:
            d_type = item.get("disruption_type")
            if d_type:
                disruption_counts[d_type] = disruption_counts.get(d_type, 0) + 1
        
        dominant_type = max(disruption_counts, key=disruption_counts.get) if disruption_counts else None
        
        return RiskSignal(
            source="news_sentiment",
            risk_score=round(risk_score, 3),
            confidence=min(0.85, 0.6 + len(news_items) * 0.01),
            disruption_type=dominant_type,
            region=None,
            factors=[
                f"Analyzed {len(news_items)} news articles",
                f"Average sentiment: {avg_sentiment:.2f}",
                f"Dominant disruption type: {dominant_type or 'General'}"
            ]
        )
    
    def analyze_historical_pattern(self, region: str, disruption_type: str) -> RiskSignal:
        """Analyze risk based on historical patterns"""
        # Simulate historical pattern analysis
        base_risk = self.regional_risk_base.get(region, 0.4)
        severity = self.severity_multipliers.get(disruption_type, 1.0)
        
        # Add seasonal factors
        month = datetime.now().month
        seasonal_factor = 1.0
        if disruption_type == "natural_disaster":
            # Higher risk during monsoon/hurricane seasons
            if month in [6, 7, 8, 9]:
                seasonal_factor = 1.3
        elif disruption_type == "transportation":
            # Higher during holiday shipping
            if month in [11, 12, 1]:
                seasonal_factor = 1.2
        
        risk_score = base_risk * severity * seasonal_factor
        risk_score = min(1.0, risk_score + random.gauss(0, 0.05))
        
        return RiskSignal(
            source="historical_pattern",
            risk_score=round(risk_score, 3),
            confidence=0.75,
            disruption_type=disruption_type,
            region=region,
            factors=[
                f"Historical base risk for {region}: {base_risk:.2f}",
                f"Seasonal adjustment: {seasonal_factor:.1f}x",
                f"Disruption severity factor: {severity:.1f}x"
            ]
        )
    
    def analyze_supplier_risk(self, suppliers: List[Dict[str, Any]]) -> RiskSignal:
        """Analyze risk from supplier concentration and health"""
        if not suppliers:
            return RiskSignal(
                source="supplier_concentration",
                risk_score=0.3,
                confidence=0.5,
                disruption_type="supplier",
                region=None,
                factors=["No supplier data available"]
            )
        
        # Concentration risk
        regions = [s.get("region") for s in suppliers]
        region_counts = {r: regions.count(r) for r in set(regions)}
        concentration = max(region_counts.values()) / len(suppliers)
        
        # Tier 1 dependency
        tier1_count = sum(1 for s in suppliers if s.get("tier") == 1)
        tier1_risk = (tier1_count / len(suppliers)) * 0.5
        
        # Critical suppliers
        critical_count = sum(1 for s in suppliers if s.get("is_critical"))
        critical_risk = (critical_count / len(suppliers)) * 0.3
        
        total_risk = (concentration * 0.4) + tier1_risk + critical_risk
        
        return RiskSignal(
            source="supplier_concentration",
            risk_score=round(min(1.0, total_risk), 3),
            confidence=0.8,
            disruption_type="supplier",
            region=max(region_counts, key=region_counts.get),
            factors=[
                f"Regional concentration: {concentration * 100:.0f}%",
                f"Tier-1 supplier exposure: {tier1_count}/{len(suppliers)}",
                f"Critical suppliers: {critical_count}"
            ]
        )
    
    def aggregate_signals(self, signals: List[RiskSignal]) -> AggregatedRisk:
        """Aggregate multiple risk signals into overall assessment"""
        if not signals:
            return AggregatedRisk(
                overall_score=0.3,
                risk_level=RiskLevel.LOW,
                confidence=0.5,
                contributing_signals=[],
                top_factors=["Insufficient data for assessment"],
                trend="stable"
            )
        
        # Weighted average of signals
        total_weight = 0
        weighted_sum = 0
        
        for signal in signals:
            weight = self.signal_weights.get(signal.source, 0.1) * signal.confidence
            weighted_sum += signal.risk_score * weight
            total_weight += weight
        
        overall_score = weighted_sum / total_weight if total_weight > 0 else 0.3
        
        # Determine risk level
        if overall_score >= 0.85:
            risk_level = RiskLevel.CRITICAL
        elif overall_score >= 0.7:
            risk_level = RiskLevel.HIGH
        elif overall_score >= 0.4:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        # Average confidence
        avg_confidence = sum(s.confidence for s in signals) / len(signals)
        
        # Collect top factors
        all_factors = []
        for signal in signals:
            all_factors.extend(signal.factors)
        top_factors = all_factors[:5]
        
        # Simulate trend
        trend = random.choice(["increasing", "stable", "decreasing"])
        if overall_score > 0.7:
            trend = random.choices(["increasing", "stable"], weights=[0.6, 0.4])[0]
        
        return AggregatedRisk(
            overall_score=round(overall_score, 3),
            risk_level=risk_level,
            confidence=round(avg_confidence, 3),
            contributing_signals=signals,
            top_factors=top_factors,
            trend=trend
        )
    
    def predict_future_risk(self, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """Generate risk predictions for future dates"""
        predictions = []
        base_risk = random.uniform(0.35, 0.55)
        
        for day in range(1, days_ahead + 1):
            # Add decreasing confidence over time
            confidence = max(0.5, 0.95 - (day * 0.015))
            
            # Add trend and randomness
            trend_factor = math.sin(day / 10) * 0.1
            random_factor = random.gauss(0, 0.05)
            
            risk = base_risk + trend_factor + random_factor
            risk = max(0, min(1, risk))
            
            predictions.append({
                "date": (datetime.utcnow() + timedelta(days=day)).strftime("%Y-%m-%d"),
                "risk_score": round(risk, 3),
                "confidence": round(confidence, 3),
                "risk_level": self._get_risk_level(risk).value
            })
        
        return predictions
    
    def _get_risk_level(self, score: float) -> RiskLevel:
        """Convert score to risk level"""
        if score >= 0.85:
            return RiskLevel.CRITICAL
        elif score >= 0.7:
            return RiskLevel.HIGH
        elif score >= 0.4:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW
    
    def generate_recommendations(self, risk: AggregatedRisk) -> List[str]:
        """Generate actionable recommendations based on risk assessment"""
        recommendations = []
        
        if risk.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            recommendations.extend([
                "🚨 Activate supply chain contingency protocols immediately",
                "📞 Contact key suppliers for status updates",
                "📦 Evaluate emergency inventory reserves",
                "🔄 Identify and qualify alternative suppliers",
            ])
        
        if risk.risk_level == RiskLevel.CRITICAL:
            recommendations.extend([
                "⚠️ Escalate to executive leadership",
                "💰 Prepare for potential expedited shipping costs",
                "📢 Draft stakeholder communication plan",
            ])
        
        if risk.risk_level == RiskLevel.MEDIUM:
            recommendations.extend([
                "📊 Increase monitoring frequency",
                "📋 Review supplier risk assessments",
                "🔍 Conduct scenario planning exercises",
            ])
        
        if risk.risk_level == RiskLevel.LOW:
            recommendations = [
                "✅ Continue standard monitoring procedures",
                "📈 Focus on long-term resilience improvements",
                "🎯 Optimize inventory levels",
            ]
        
        return recommendations[:5]


# Singleton instance
_predictor = None

def get_risk_predictor() -> RiskPredictor:
    """Get the risk predictor singleton"""
    global _predictor
    if _predictor is None:
        _predictor = RiskPredictor()
    return _predictor
