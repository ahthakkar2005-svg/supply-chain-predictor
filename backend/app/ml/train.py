"""
ML Training Pipeline
- Prophet time-series forecasting for risk_score
- XGBoost gradient-boosted classifier for disruption risk
- Isotonic regression confidence calibration
- MLflow experiment tracking & model versioning

Usage:
    python -m app.ml.train                # train both models
    python -m app.ml.train --model prophet # train only Prophet
    python -m app.ml.train --model xgboost # train only XGBoost
"""
import argparse
import json
import logging
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Prophet Training
# ---------------------------------------------------------------------------
def train_prophet(csv_path: Optional[str] = None) -> Dict[str, Any]:
    """Train a Prophet model on daily aggregated risk scores."""
    from prophet import Prophet
    from app.ml.feature_engineering import load_disruption_csv, build_prophet_df

    logger.info("Loading data for Prophet training...")
    df = load_disruption_csv(csv_path)
    prophet_df = build_prophet_df(df)

    logger.info(f"Training Prophet on {len(prophet_df)} daily observations...")
    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        changepoint_prior_scale=0.05,
        seasonality_prior_scale=10.0,
        interval_width=0.90,
    )
    model.fit(prophet_df)

    # In-sample evaluation
    forecast = model.predict(prophet_df)
    y_true = prophet_df["y"].values
    y_pred = forecast["yhat"].values
    mae = float(np.mean(np.abs(y_true - y_pred)))
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

    # Save model
    model_path = MODEL_DIR / "prophet_model.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(model, f)

    metrics = {
        "model": "prophet",
        "observations": len(prophet_df),
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "model_path": str(model_path),
        "trained_at": datetime.utcnow().isoformat(),
    }

    # MLflow logging (optional)
    _log_to_mlflow("prophet-risk-forecast", metrics, model_path)

    logger.info(f"Prophet trained: MAE={mae:.4f}, RMSE={rmse:.4f}")
    return metrics


# ---------------------------------------------------------------------------
# XGBoost Training
# ---------------------------------------------------------------------------
def train_xgboost(csv_path: Optional[str] = None) -> Dict[str, Any]:
    """Train XGBoost on tabular disruption features."""
    from xgboost import XGBRegressor
    from sklearn.model_selection import cross_val_score
    from sklearn.isotonic import IsotonicRegression

    from app.ml.feature_engineering import load_disruption_csv, build_xgboost_features

    logger.info("Loading data for XGBoost training...")
    df = load_disruption_csv(csv_path)
    X, y = build_xgboost_features(df)

    logger.info(f"Training XGBoost on {len(X)} samples, {X.shape[1]} features...")
    model = XGBRegressor(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=1.0,
        random_state=42,
        objective="reg:squarederror",
    )
    model.fit(X, y)

    # Cross-validated metrics
    cv_scores = cross_val_score(model, X, y, cv=5, scoring="neg_mean_absolute_error")
    cv_mae = float(-cv_scores.mean())
    cv_std = float(cv_scores.std())

    # Feature importance
    importance = dict(zip(X.columns, model.feature_importances_.tolist()))
    top_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:10]

    # Isotonic calibration on predictions
    y_pred = model.predict(X)
    y_pred_clipped = np.clip(y_pred, 0, 1)

    calibrator = IsotonicRegression(y_min=0, y_max=1, out_of_bounds="clip")
    calibrator.fit(y_pred_clipped, y)

    # Save model + calibrator
    model_path = MODEL_DIR / "xgboost_model.pkl"
    calibrator_path = MODEL_DIR / "isotonic_calibrator.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    with open(calibrator_path, "wb") as f:
        pickle.dump(calibrator, f)

    # Save feature importance report
    importance_path = MODEL_DIR / "feature_importance.json"
    with open(importance_path, "w") as f:
        json.dump(
            {"top_features": [{"name": n, "importance": round(v, 4)} for n, v in top_features],
             "all_features": {k: round(v, 4) for k, v in importance.items()}},
            f, indent=2,
        )

    metrics = {
        "model": "xgboost",
        "samples": len(X),
        "features": X.shape[1],
        "cv_mae": round(cv_mae, 4),
        "cv_std": round(cv_std, 4),
        "top_features": [n for n, _ in top_features[:5]],
        "model_path": str(model_path),
        "calibrator_path": str(calibrator_path),
        "trained_at": datetime.utcnow().isoformat(),
    }

    _log_to_mlflow("xgboost-risk-model", metrics, model_path)

    logger.info(f"XGBoost trained: CV-MAE={cv_mae:.4f} ± {cv_std:.4f}")
    logger.info(f"Top features: {[n for n, _ in top_features[:5]]}")
    return metrics


# ---------------------------------------------------------------------------
# MLflow integration (optional — gracefully degrades)
# ---------------------------------------------------------------------------
def _log_to_mlflow(experiment_name: str, metrics: Dict, model_path: Path):
    """Log training run to MLflow if available."""
    try:
        import mlflow

        mlflow.set_experiment(experiment_name)
        with mlflow.start_run():
            for key, value in metrics.items():
                if isinstance(value, (int, float)):
                    mlflow.log_metric(key, value)
                elif isinstance(value, str):
                    mlflow.log_param(key, value)
            mlflow.log_artifact(str(model_path))
            logger.info(f"MLflow run logged to experiment '{experiment_name}'")
    except ImportError:
        logger.info("MLflow not installed — skipping experiment tracking")
    except Exception as e:
        logger.warning(f"MLflow logging failed (non-fatal): {e}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description="Train supply-chain risk models")
    parser.add_argument("--model", choices=["prophet", "xgboost", "all"], default="all")
    parser.add_argument("--data", type=str, default=None, help="Path to CSV training data")
    args = parser.parse_args()

    results = {}
    if args.model in ("prophet", "all"):
        results["prophet"] = train_prophet(args.data)
    if args.model in ("xgboost", "all"):
        results["xgboost"] = train_xgboost(args.data)

    print("\n=== Training Complete ===")
    for name, m in results.items():
        print(f"\n{name.upper()}:")
        for k, v in m.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
