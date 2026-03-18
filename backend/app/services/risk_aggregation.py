"""
Risk Aggregation Service — FIX 5
Orchestrates risk signal collection and aggregation from multiple sources.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.ml.predictor import RiskPredictor, RiskSignal, AggregatedRisk

logger = logging.getLogger(__name__)


class RiskAggregationService:
    """
    Collects risk signals from news, suppliers, weather, and historical data,
    then aggregates them into an overall risk assessment.
    """

    def __init__(self, predictor: Optional[RiskPredictor] = None):
        self._predictor = predictor

    @property
    def predictor(self) -> RiskPredictor:
        if self._predictor is None:
            from app.ml import get_risk_predictor
            self._predictor = get_risk_predictor()
        return self._predictor

    def assess_risk(
        self,
        news_items: List[Dict[str, Any]],
        suppliers: List[Dict[str, Any]],
        region: str = "Asia Pacific",
        disruption_type: str = "geopolitical",
    ) -> AggregatedRisk:
        """
        Run full risk assessment across all signal types.
        """
        signals: List[RiskSignal] = []

        # 1. News sentiment signal
        news_signal = self.predictor.analyze_news_risk(news_items)
        signals.append(news_signal)

        # 2. Supplier concentration signal
        supplier_signal = self.predictor.analyze_supplier_risk(suppliers)
        signals.append(supplier_signal)

        # 3. Historical pattern signal
        historical_signal = self.predictor.analyze_historical_pattern(region, disruption_type)
        signals.append(historical_signal)

        # Aggregate
        aggregated = self.predictor.aggregate_signals(signals)
        return aggregated

    def get_recommendations(self, risk: AggregatedRisk) -> List[str]:
        """Generate recommendations for a given risk assessment."""
        return self.predictor.generate_recommendations(risk)
