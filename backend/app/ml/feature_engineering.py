"""
Feature Engineering for Supply Chain Risk Models
Transforms raw GDELT-style disruption data into features for Prophet and XGBoost.
"""
import math
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

# ---------- region / disruption one-hot mappings ----------
REGIONS = [
    "Asia Pacific", "Europe", "North America",
    "Latin America", "Middle East & Africa",
]

DISRUPTION_TYPES = [
    "geopolitical", "transportation", "economic", "natural_disaster",
    "labor", "cyber", "supplier", "conflict",
]


def load_disruption_csv(path: Optional[str] = None) -> pd.DataFrame:
    """Load GDELT-style disruption CSV and clean it."""
    csv_path = Path(path) if path else DATA_DIR / "sample_disruption_data.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Training data not found at {csv_path}")

    df = pd.read_csv(csv_path, parse_dates=["date"])
    df.sort_values("date", inplace=True)
    df.reset_index(drop=True, inplace=True)

    # Ensure required columns
    required = [
        "date", "risk_score", "news_sentiment", "news_volume",
        "supplier_concentration", "commodity_price_delta",
        "shipping_delay_index", "weather_severity", "geopolitical_tension",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in training data: {missing}")

    return df


def build_prophet_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a Prophet-compatible dataframe with ds/y columns.
    Aggregates daily risk_score as the target time-series.
    """
    daily = df.groupby("date").agg({"risk_score": "mean"}).reset_index()
    daily.columns = ["ds", "y"]
    daily["ds"] = pd.to_datetime(daily["ds"])
    return daily


def build_xgboost_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Build tabular feature matrix for XGBoost.
    Returns (X, y) where y is risk_score.
    """
    feat = df.copy()

    # Calendar features
    feat["day_of_week"] = feat["date"].dt.dayofweek
    feat["month"] = feat["date"].dt.month
    feat["quarter"] = feat["date"].dt.quarter
    feat["day_of_year"] = feat["date"].dt.dayofyear
    feat["is_weekend"] = (feat["day_of_week"] >= 5).astype(int)

    # Cyclical encoding for month
    feat["month_sin"] = np.sin(2 * math.pi * feat["month"] / 12)
    feat["month_cos"] = np.cos(2 * math.pi * feat["month"] / 12)

    # One-hot encode region
    for r in REGIONS:
        feat[f"region_{r.lower().replace(' ', '_').replace('&', 'and')}"] = (
            feat["region"] == r
        ).astype(int)

    # One-hot encode disruption_type
    for dt in DISRUPTION_TYPES:
        feat[f"dtype_{dt}"] = (feat["disruption_type"] == dt).astype(int)

    # Lag features (rolling averages)
    feat.sort_values("date", inplace=True)
    feat["risk_lag_1"] = feat["risk_score"].shift(1).fillna(feat["risk_score"].mean())
    feat["risk_lag_3"] = (
        feat["risk_score"].rolling(3, min_periods=1).mean()
    )
    feat["risk_lag_7"] = (
        feat["risk_score"].rolling(7, min_periods=1).mean()
    )
    feat["sentiment_lag_3"] = (
        feat["news_sentiment"].rolling(3, min_periods=1).mean()
    )
    feat["volume_lag_3"] = (
        feat["news_volume"].rolling(3, min_periods=1).mean()
    )

    # Interaction features
    feat["sentiment_x_volume"] = feat["news_sentiment"] * feat["news_volume"]
    feat["geo_x_shipping"] = feat["geopolitical_tension"] * feat["shipping_delay_index"]

    # Target
    y = feat["risk_score"]

    # Select feature columns (drop non-feature columns)
    drop_cols = ["date", "region", "disruption_type", "risk_score"]
    X = feat.drop(columns=drop_cols, errors="ignore")

    return X, y


def get_feature_names() -> List[str]:
    """Return the ordered list of feature names for documentation."""
    base = [
        "news_sentiment", "news_volume", "supplier_concentration",
        "commodity_price_delta", "shipping_delay_index",
        "weather_severity", "geopolitical_tension",
    ]
    calendar = [
        "day_of_week", "month", "quarter", "day_of_year", "is_weekend",
        "month_sin", "month_cos",
    ]
    region_cols = [
        f"region_{r.lower().replace(' ', '_').replace('&', 'and')}"
        for r in REGIONS
    ]
    dtype_cols = [f"dtype_{dt}" for dt in DISRUPTION_TYPES]
    lag_cols = [
        "risk_lag_1", "risk_lag_3", "risk_lag_7",
        "sentiment_lag_3", "volume_lag_3",
    ]
    interaction = ["sentiment_x_volume", "geo_x_shipping"]
    return base + calendar + region_cols + dtype_cols + lag_cols + interaction
