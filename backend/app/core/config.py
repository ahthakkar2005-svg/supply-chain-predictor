"""
Core application configuration
"""
from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "Supply Chain Disruption Predictor"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # API Keys
    NEWS_API_KEY: Optional[str] = None
    TWITTER_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    OPENWEATHER_API_KEY: Optional[str] = None
    
    # Real-time Settings
    REALTIME_INTERVAL: int = 5  # seconds between risk drift ticks
    NEWS_FETCH_INTERVAL: int = 60  # seconds between news API fetches
    
    # Database
    DATABASE_URL: str = "sqlite:///./supply_chain.db"
    MONGODB_URL: str = "mongodb://localhost:27017"
    
    # ML Model Settings
    MODEL_UPDATE_INTERVAL: int = 3600  # seconds
    PREDICTION_HORIZON_DAYS: int = 30
    RISK_THRESHOLD_HIGH: float = 0.7
    RISK_THRESHOLD_MEDIUM: float = 0.4
    
    # Alert Settings
    ALERT_EMAIL_ENABLED: bool = False
    ALERT_EMAIL_RECIPIENTS: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Risk level definitions
RISK_LEVELS = {
    "CRITICAL": {"min": 0.85, "color": "#FF4757", "label": "Critical"},
    "HIGH": {"min": 0.7, "color": "#FFA502", "label": "High"},
    "MEDIUM": {"min": 0.4, "color": "#FFEAA7", "label": "Medium"},
    "LOW": {"min": 0.0, "color": "#26DE81", "label": "Low"},
}

# Supply chain categories
SUPPLY_CHAIN_CATEGORIES = [
    "Raw Materials",
    "Manufacturing",
    "Logistics",
    "Warehousing",
    "Distribution",
    "Retail",
    "Suppliers",
]

# Disruption types
DISRUPTION_TYPES = [
    "Natural Disaster",
    "Geopolitical",
    "Economic",
    "Pandemic",
    "Labor Strike",
    "Cyber Attack",
    "Transportation",
    "Regulatory",
    "Supplier Failure",
]

# Geographic regions
REGIONS = [
    {"code": "NA", "name": "North America", "lat": 40.0, "lng": -100.0},
    {"code": "EU", "name": "Europe", "lat": 50.0, "lng": 10.0},
    {"code": "APAC", "name": "Asia Pacific", "lat": 35.0, "lng": 105.0},
    {"code": "SA", "name": "South Asia (India)", "lat": 20.5, "lng": 79.0},
    {"code": "LATAM", "name": "Latin America", "lat": -15.0, "lng": -60.0},
    {"code": "MEA", "name": "Middle East & Africa", "lat": 25.0, "lng": 45.0},
]
