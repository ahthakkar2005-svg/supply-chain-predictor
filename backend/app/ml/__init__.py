"""ML module for prediction and forecasting"""
from .predictor import RiskPredictor, RiskSignal, AggregatedRisk, LowConfidenceResult


# Singleton — will be replaced by app.state DI in FIX 8
_predictor = None


def get_risk_predictor(config=None) -> RiskPredictor:
    """Get the risk predictor singleton."""
    global _predictor
    if _predictor is None:
        _predictor = RiskPredictor(config=config)
    return _predictor
