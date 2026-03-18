"""
Anomaly Detection — FIX 19
Uses Isolation Forest from scikit-learn (fallback if PyOD not installed).
Flags when incoming data deviates significantly from training distribution.
"""
import logging
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "models"


class AnomalyDetector:
    """
    Detects anomalous incoming data using Isolation Forest.
    Triggers HIGH_UNCERTAINTY alerts when anomaly score exceeds threshold.
    """

    def __init__(self, contamination: float = 0.1, threshold: float = -0.3):
        self._model = None
        self._threshold = threshold
        self._contamination = contamination
        self._is_fitted = False
        self._load_or_init()

    def _load_or_init(self):
        """Load pre-trained detector or create new one."""
        model_path = MODEL_DIR / "anomaly_detector.pkl"
        if model_path.exists():
            try:
                with open(model_path, "rb") as f:
                    self._model = pickle.load(f)
                self._is_fitted = True
                logger.info("✅ Anomaly detector loaded from disk")
                return
            except Exception as e:
                logger.warning(f"Failed to load anomaly detector: {e}")

        # Initialize new model
        try:
            from pyod.models.ecod import ECOD
            self._model = ECOD(contamination=self._contamination)
            logger.info("Initialized ECOD anomaly detector (PyOD)")
        except ImportError:
            from sklearn.ensemble import IsolationForest
            self._model = IsolationForest(
                contamination=self._contamination,
                random_state=42,
                n_estimators=100,
            )
            logger.info("Initialized IsolationForest anomaly detector (sklearn)")

    def fit(self, X: np.ndarray):
        """Fit the anomaly detector on training data."""
        try:
            self._model.fit(X)
            self._is_fitted = True

            # Persist
            MODEL_DIR.mkdir(parents=True, exist_ok=True)
            model_path = MODEL_DIR / "anomaly_detector.pkl"
            with open(model_path, "wb") as f:
                pickle.dump(self._model, f)
            logger.info(f"Anomaly detector fitted on {X.shape[0]} samples")
        except Exception as e:
            logger.error(f"Anomaly detector fitting failed: {e}")

    def detect(self, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Check if a single data point is anomalous.
        Returns anomaly score and flag.
        """
        if not self._is_fitted:
            return {
                "is_anomaly": False,
                "anomaly_score": 0.0,
                "high_uncertainty": False,
                "message": "Anomaly detector not trained",
            }

        try:
            X = np.array([list(features.values())])

            # PyOD vs sklearn have different interfaces
            if hasattr(self._model, "decision_function"):
                score = float(self._model.decision_function(X)[0])
            else:
                score = float(self._model.score_samples(X)[0])

            is_anomaly = score < self._threshold
            high_uncertainty = score < (self._threshold * 1.5)

            result = {
                "is_anomaly": is_anomaly,
                "anomaly_score": round(score, 4),
                "threshold": self._threshold,
                "high_uncertainty": high_uncertainty,
            }

            if high_uncertainty:
                result["message"] = "HIGH_UNCERTAINTY: Data significantly deviates from training distribution"
                logger.warning(f"Anomaly detected: score={score:.4f}, threshold={self._threshold}")

            return result

        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            return {
                "is_anomaly": False,
                "anomaly_score": 0.0,
                "high_uncertainty": False,
                "error": str(e),
            }

    def batch_detect(self, feature_list: List[Dict[str, float]]) -> List[Dict[str, Any]]:
        """Check multiple data points for anomalies."""
        return [self.detect(f) for f in feature_list]


# Singleton
_detector: Optional[AnomalyDetector] = None


def get_anomaly_detector() -> AnomalyDetector:
    global _detector
    if _detector is None:
        _detector = AnomalyDetector()
    return _detector
