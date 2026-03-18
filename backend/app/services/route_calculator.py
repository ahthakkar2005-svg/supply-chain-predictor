"""
Route Calculator Service
Analyzes transit delays, distances, costs, and risks using geographical tracking and live weather.
"""
import math
import logging
from typing import Dict, List, Tuple
from app.models.schemas import RouteAnalysisRequest, RouteAnalysisResponse, RiskLevel
from app.services.weather_service import SUPPLY_CHAIN_HUBS, get_weather_service

logger = logging.getLogger(__name__)

# Constants for rough maritime calculation
OCEAN_FREIGHT_SPEED_KMPH = 35.0  # Approx 19 knots
BASE_COST_PER_KM = 0.50          # Base ocean freight rate per km

# Regional penalty multipliers for geopolitical disruptions or piracy risks
REGIONAL_RISK_DELAY_PENALTIES = {
    "Middle East & Africa": 4.0,  # e.g., Red Sea shipping attacks
    "Asia Pacific": 1.5,
    "Europe": 1.0,
    "North America": 1.0,
    "South Asia (India)": 1.2,
}


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance in kilometers between two points on Earth."""
    r = 6371.0 # Earth radius in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def _get_hub_by_name(name: str) -> Dict:
    name_lower = name.lower()
    for hub in SUPPLY_CHAIN_HUBS:
        if hub["name"].lower() == name_lower:
            return hub
    raise ValueError(f"Port '{name}' is not currently monitored in the network.")


class RouteCalculator:
    """Simulates realistic route transit metrics and delay estimations."""
    
    @staticmethod
    def analyze_route(request: RouteAnalysisRequest) -> RouteAnalysisResponse:
        origin = _get_hub_by_name(request.origin_port)
        dest = _get_hub_by_name(request.destination_port)
        
        # 1. Base Distance & Time
        distance_km = _haversine(origin["lat"], origin["lon"], dest["lat"], dest["lon"])
        base_transit_hours = distance_km / OCEAN_FREIGHT_SPEED_KMPH
        base_transit_days = max(1, int(round(base_transit_hours / 24)))
        
        # 2. Base Cost
        base_cost = distance_km * BASE_COST_PER_KM
        
        delay_days = 0
        final_cost = base_cost
        delay_factors = []
        recommendations = []
        
        # 3. Geo-political Regional Delay Risks
        origin_regional_penalty = REGIONAL_RISK_DELAY_PENALTIES.get(origin["region"], 1.0)
        dest_regional_penalty = REGIONAL_RISK_DELAY_PENALTIES.get(dest["region"], 1.0)
        
        if dest_regional_penalty > 1.5 or origin_regional_penalty > 1.5:
            added_delay = int(max(origin_regional_penalty, dest_regional_penalty))
            delay_days += added_delay
            final_cost += (added_delay * 1500) # Demurrage/Insurance costs
            delay_factors.append(f"Geopolitical instability in {dest['region']} or {origin['region']}.")
            recommendations.append("Secure high-risk maritime insurance wrapper.")
            
        # 4. Live Weather Disruptions
        weather_service = get_weather_service()
        conditions = weather_service.get_current_conditions()
        
        for port in [origin, dest]:
            port_weather = conditions.get(port["name"])
            if port_weather:
                weather_id = port_weather.get("condition_id", 800)
                wind = port_weather.get("wind_speed", 0)
                
                if wind > 15 or (200 <= weather_id < 600):
                    delay_days += 2
                    delay_factors.append(f"Severe weather ({port_weather.get('condition', 'Storm')}) delaying operations at {port['name']}.")
                    recommendations.append(f"Expedite land-transit scheduling at {port['name']} to off-set storm loading delays.")
                    
        # 5. Compile Risk Level
        risk_level = RiskLevel.LOW
        if delay_days >= 4:
            risk_level = RiskLevel.CRITICAL
        elif delay_days >= 2:
            risk_level = RiskLevel.HIGH
            
        return RouteAnalysisResponse(
            origin_port=origin["name"],
            destination_port=dest["name"],
            distance_km=round(distance_km, 2),
            base_transit_days=base_transit_days,
            predicted_delay_days=delay_days,
            final_eta_days=base_transit_days + delay_days,
            base_cost_usd=round(base_cost, 2),
            final_cost_usd=round(final_cost, 2),
            risk_level=risk_level,
            delay_factors=delay_factors,
            recommendations=recommendations or ["Route is optimal. Proceed with standard shipping schedules."]
        )
