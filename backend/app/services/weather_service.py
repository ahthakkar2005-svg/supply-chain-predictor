"""
Weather Service - Fetches real weather data from OpenWeatherMap
Monitors major supply chain ports/hubs for severe weather that could cause disruptions
Falls back to simulated data when API key is not configured
"""
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Optional
import random

import httpx

from app.core.config import get_settings
from app.models import Alert, RiskLevel, DisruptionType

logger = logging.getLogger(__name__)

# Major supply chain hub locations to monitor
SUPPLY_CHAIN_HUBS = [
    {"name": "Shanghai", "lat": 31.23, "lon": 121.47, "region": "Asia Pacific", "type": "port"},
    {"name": "Singapore", "lat": 1.35, "lon": 103.82, "region": "Asia Pacific", "type": "port"},
    {"name": "Rotterdam", "lat": 51.92, "lon": 4.48, "region": "Europe", "type": "port"},
    {"name": "Los Angeles", "lat": 33.74, "lon": -118.27, "region": "North America", "type": "port"},
    {"name": "Hamburg", "lat": 53.55, "lon": 9.99, "region": "Europe", "type": "port"},
    {"name": "Shenzhen", "lat": 22.54, "lon": 114.06, "region": "Asia Pacific", "type": "manufacturing"},
    {"name": "Dubai", "lat": 25.20, "lon": 55.27, "region": "Middle East & Africa", "type": "hub"},
    {"name": "New York", "lat": 40.71, "lon": -74.01, "region": "North America", "type": "hub"},
    # India - Major Supply Chain Hubs
    {"name": "Mumbai (JNPT)", "lat": 18.95, "lon": 72.95, "region": "South Asia (India)", "type": "port"},
    {"name": "Chennai", "lat": 13.08, "lon": 80.29, "region": "South Asia (India)", "type": "port"},
    {"name": "Delhi NCR", "lat": 28.61, "lon": 77.23, "region": "South Asia (India)", "type": "manufacturing"},
    {"name": "Kolkata", "lat": 22.57, "lon": 88.36, "region": "South Asia (India)", "type": "port"},
    {"name": "Mundra (Gujarat)", "lat": 22.84, "lon": 69.72, "region": "South Asia (India)", "type": "port"},
    {"name": "Visakhapatnam", "lat": 17.69, "lon": 83.22, "region": "South Asia (India)", "type": "port"},
]

# Weather condition severity mapping
SEVERE_WEATHER_IDS = {
    # Thunderstorm group (200-299)
    range(200, 300): {"severity": "high", "type": "thunderstorm"},
    # Drizzle/Rain group (300-599)
    range(500, 600): {"severity": "medium", "type": "rain"},
    # Heavy rain
    range(502, 505): {"severity": "high", "type": "heavy_rain"},
    # Snow (600-699)
    range(600, 700): {"severity": "medium", "type": "snow"},
    # Atmosphere (700-799) - fog, haze, etc.
    range(700, 800): {"severity": "low", "type": "fog"},
    # Extreme conditions
    range(900, 907): {"severity": "critical", "type": "extreme"},
}


def _get_weather_severity(weather_id: int) -> Dict:
    """Get severity info from weather condition ID"""
    for id_range, info in SEVERE_WEATHER_IDS.items():
        if weather_id in id_range:
            return info
    return {"severity": "low", "type": "normal"}


def _weather_to_risk_level(severity: str) -> RiskLevel:
    """Convert weather severity to risk level"""
    mapping = {
        "critical": RiskLevel.CRITICAL,
        "high": RiskLevel.HIGH,
        "medium": RiskLevel.MEDIUM,
        "low": RiskLevel.LOW,
    }
    return mapping.get(severity, RiskLevel.LOW)


class WeatherService:
    """Fetches real weather data from OpenWeatherMap for supply chain hubs"""

    def __init__(self):
        self.settings = get_settings()
        self.api_key = getattr(self.settings, 'OPENWEATHER_API_KEY', None)
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self._current_conditions: Dict[str, Dict] = {}
        self._active_alerts: List[Alert] = []

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def fetch_weather_alerts(self) -> List[Alert]:
        """Fetch weather for all supply chain hubs, return alerts for severe conditions"""
        if not self.is_configured:
            logger.debug("OpenWeatherMap key not set, using simulated weather")
            return self._generate_mock_weather_alerts()

        alerts = []
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                for hub in SUPPLY_CHAIN_HUBS:
                    try:
                        weather = await self._fetch_hub_weather(client, hub)
                        if weather:
                            self._current_conditions[hub["name"]] = weather
                            alert = self._evaluate_weather_risk(hub, weather)
                            if alert:
                                alerts.append(alert)
                    except Exception as e:
                        logger.warning(f"Weather fetch failed for {hub['name']}: {e}")

            self._active_alerts = alerts
            if alerts:
                logger.info(f"Generated {len(alerts)} weather alerts from real data")

        except Exception as e:
            logger.warning(f"OpenWeatherMap fetch failed: {e}, using mock data")
            return self._generate_mock_weather_alerts()

        return alerts

    async def _fetch_hub_weather(self, client: httpx.AsyncClient, hub: Dict) -> Optional[Dict]:
        """Fetch current weather for a specific hub"""
        params = {
            "lat": hub["lat"],
            "lon": hub["lon"],
            "appid": self.api_key,
            "units": "metric",
        }

        response = await client.get(f"{self.base_url}/weather", params=params)
        response.raise_for_status()
        data = response.json()

        weather_info = data.get("weather", [{}])[0]
        main = data.get("main", {})
        wind = data.get("wind", {})

        return {
            "condition_id": weather_info.get("id", 800),
            "condition": weather_info.get("main", "Clear"),
            "description": weather_info.get("description", ""),
            "temp": main.get("temp", 20),
            "humidity": main.get("humidity", 50),
            "wind_speed": wind.get("speed", 0),
            "wind_gust": wind.get("gust", 0),
            "visibility": data.get("visibility", 10000),
        }

    def _evaluate_weather_risk(self, hub: Dict, weather: Dict) -> Optional[Alert]:
        """Evaluate if weather conditions pose supply chain risk"""
        severity_info = _get_weather_severity(weather["condition_id"])
        wind_speed = weather.get("wind_speed", 0)

        # Upgrade severity for extreme wind
        if wind_speed > 20:  # m/s (~45 mph)
            severity_info = {"severity": "high", "type": "high_wind"}
        if wind_speed > 30:  # m/s (~67 mph)
            severity_info = {"severity": "critical", "type": "extreme_wind"}

        # Only alert on medium+ severity
        if severity_info["severity"] in ("low",):
            return None

        risk_level = _weather_to_risk_level(severity_info["severity"])

        title = f"Weather Alert: {weather['condition']} at {hub['name']}"
        message = (
            f"Severe weather detected at {hub['name']} ({hub['region']}): "
            f"{weather['description']}. "
            f"Temperature: {weather['temp']}°C, Wind: {wind_speed} m/s. "
            f"This may impact {hub['type']} operations and supply chain logistics."
        )

        return Alert(
            id=str(uuid.uuid4()),
            created_at=datetime.utcnow(),
            title=title,
            message=message,
            risk_level=risk_level,
            disruption_type=DisruptionType.NATURAL_DISASTER,
            region=hub["region"],
            is_read=False,
            is_acknowledged=False,
        )

    def _generate_mock_weather_alerts(self) -> List[Alert]:
        """Generate simulated weather alerts"""
        # Small chance of generating a mock weather alert
        if random.random() > 0.3:
            return []

        hub = random.choice(SUPPLY_CHAIN_HUBS)
        scenarios = [
            {
                "condition": "Tropical Storm",
                "desc": "tropical storm with heavy rainfall",
                "severity": RiskLevel.HIGH,
            },
            {
                "condition": "Heavy Rain",
                "desc": "sustained heavy rainfall causing potential flooding",
                "severity": RiskLevel.MEDIUM,
            },
            {
                "condition": "High Winds",
                "desc": "sustained high winds exceeding 50 km/h",
                "severity": RiskLevel.MEDIUM,
            },
        ]
        scenario = random.choice(scenarios)

        return [Alert(
            id=str(uuid.uuid4()),
            created_at=datetime.utcnow(),
            title=f"Weather Alert: {scenario['condition']} at {hub['name']}",
            message=(
                f"Simulated weather alert: {scenario['desc']} detected at "
                f"{hub['name']} ({hub['region']}). This may impact "
                f"{hub['type']} operations and supply chain logistics."
            ),
            risk_level=scenario["severity"],
            disruption_type=DisruptionType.NATURAL_DISASTER,
            region=hub["region"],
            is_read=False,
            is_acknowledged=False,
        )]

    def get_current_conditions(self) -> Dict[str, Dict]:
        """Get cached weather conditions for all monitored hubs"""
        return self._current_conditions

    def get_active_alerts(self) -> List[Alert]:
        """Get currently active weather alerts"""
        return self._active_alerts


# Singleton
_weather_service: Optional[WeatherService] = None


def get_weather_service() -> WeatherService:
    global _weather_service
    if _weather_service is None:
        _weather_service = WeatherService()
    return _weather_service
