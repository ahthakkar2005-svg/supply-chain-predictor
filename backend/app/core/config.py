"""
Core application configuration — Production-grade
- Uses pydantic-settings with SecretStr for API keys
- Environment-aware (dev / staging / production)
- Optional AWS Secrets Manager loader
"""
import logging
from functools import lru_cache
from typing import List, Optional

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ---- Application ----
    APP_NAME: str = "Supply Chain Disruption Predictor"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    ENV: str = "development"  # development | staging | production

    # ---- API Keys (SecretStr — never logged / serialised) ----
    NEWS_API_KEY: Optional[SecretStr] = None
    TWITTER_API_KEY: Optional[SecretStr] = None
    OPENAI_API_KEY: Optional[SecretStr] = None
    OPENWEATHER_API_KEY: Optional[SecretStr] = None

    # ---- JWT ----
    JWT_SECRET_KEY: SecretStr = SecretStr("change-this-to-a-random-64-char-secret")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ---- Real-time ----
    REALTIME_INTERVAL: int = 5
    NEWS_FETCH_INTERVAL: int = 60

    # ---- Database ----
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "supply_chain_predictor"

    # ---- Redis ----
    REDIS_URL: str = "redis://localhost:6379/0"

    # ---- ML ----
    MODEL_UPDATE_INTERVAL: int = 3600
    PREDICTION_HORIZON_DAYS: int = 30
    RISK_THRESHOLD_HIGH: float = 0.7
    RISK_THRESHOLD_MEDIUM: float = 0.4

    # ---- Alerts ----
    ALERT_EMAIL_ENABLED: bool = False
    ALERT_EMAIL_RECIPIENTS: str = ""
    SENDGRID_API_KEY: Optional[SecretStr] = None
    SLACK_WEBHOOK_URL: Optional[str] = None
    TEAMS_WEBHOOK_URL: Optional[str] = None

    # ---- CORS ----
    CORS_ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # ---- Stripe ----
    STRIPE_SECRET_KEY: Optional[SecretStr] = None
    STRIPE_WEBHOOK_SECRET: Optional[SecretStr] = None

    # ---- Observability ----
    SENTRY_DSN: Optional[str] = None
    JAEGER_ENDPOINT: Optional[str] = None

    # ---- AWS Secrets Manager (optional) ----
    AWS_SECRETS_NAME: Optional[str] = None
    AWS_REGION: str = "us-east-1"

    @field_validator("ENV")
    @classmethod
    def validate_env(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"ENV must be one of {allowed}, got '{v}'")
        return v

    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS_ALLOWED_ORIGINS into a list."""
        return [o.strip() for o in self.CORS_ALLOWED_ORIGINS.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


def _load_aws_secrets(settings: Settings) -> Settings:
    """
    Optionally load secrets from AWS Secrets Manager.
    Overrides local .env values when AWS_SECRETS_NAME is set.
    """
    if not settings.AWS_SECRETS_NAME:
        return settings

    try:
        import boto3
        import json

        client = boto3.client("secretsmanager", region_name=settings.AWS_REGION)
        response = client.get_secret_value(SecretId=settings.AWS_SECRETS_NAME)
        secrets = json.loads(response["SecretString"])

        # Override settings with AWS-stored secrets
        overrides = {}
        for key, value in secrets.items():
            if hasattr(settings, key) and value:
                overrides[key] = value

        if overrides:
            settings = settings.model_copy(update=overrides)
            logger.info(f"Loaded {len(overrides)} secrets from AWS Secrets Manager")

    except ImportError:
        logger.warning("boto3 not installed — skipping AWS Secrets Manager")
    except Exception as e:
        logger.error(f"Failed to load AWS secrets: {e}")

    return settings


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance with optional AWS overlay."""
    settings = Settings()
    settings = _load_aws_secrets(settings)
    return settings


# ---------- Constants (unchanged from original) ----------

RISK_LEVELS = {
    "CRITICAL": {"min": 0.85, "color": "#FF4757", "label": "Critical"},
    "HIGH": {"min": 0.7, "color": "#FFA502", "label": "High"},
    "MEDIUM": {"min": 0.4, "color": "#FFEAA7", "label": "Medium"},
    "LOW": {"min": 0.0, "color": "#26DE81", "label": "Low"},
}

SUPPLY_CHAIN_CATEGORIES = [
    "Raw Materials", "Manufacturing", "Logistics",
    "Warehousing", "Distribution", "Retail", "Suppliers",
]

DISRUPTION_TYPES = [
    "Natural Disaster", "Geopolitical", "Economic", "Pandemic",
    "Labor Strike", "Cyber Attack", "Transportation", "Regulatory",
    "Supplier Failure",
]

REGIONS = [
    {"code": "NA", "name": "North America", "lat": 40.0, "lng": -100.0},
    {"code": "EU", "name": "Europe", "lat": 50.0, "lng": 10.0},
    {"code": "APAC", "name": "Asia Pacific", "lat": 35.0, "lng": 105.0},
    {"code": "SA", "name": "South Asia (India)", "lat": 20.5, "lng": 79.0},
    {"code": "LATAM", "name": "Latin America", "lat": -15.0, "lng": -60.0},
    {"code": "MEA", "name": "Middle East & Africa", "lat": 25.0, "lng": 45.0},
]
