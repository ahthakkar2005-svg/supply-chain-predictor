"""
Data Simulation Service - Generates realistic supply chain data for MVP demo
Uses mock data when API keys are not available
"""
import random
import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import math

logger = logging.getLogger(__name__)


from app.models import (
    NewsArticle, Prediction, Alert, Supplier, 
    RiskLevel, DisruptionType, RegionRisk, RiskMetric, DashboardSummary
)
from app.core.config import REGIONS, DISRUPTION_TYPES, SUPPLY_CHAIN_CATEGORIES


# Realistic news headlines for supply chain disruptions
NEWS_TEMPLATES = {
    "natural_disaster": [
        "Typhoon {name} disrupts shipping routes in {region}, delays expected for 2+ weeks",
        "Earthquake magnitude {magnitude} strikes {location}, manufacturing facilities damaged",
        "Severe flooding in {region} halts production at major electronics plants",
        "Drought conditions impacting agricultural supply chains in {region}",
        "Wildfire forces evacuation near key semiconductor facilities in {location}",
    ],
    "geopolitical": [
        "New tariffs imposed on {product} imports from {region}, prices expected to surge",
        "Trade negotiations stall between {country1} and {country2}, supply uncertainty rises",
        "Sanctions on {country} impact rare earth material availability",
        "Border restrictions tighten in {region}, logistics delays mounting",
        "Political instability in {country} threatens key supplier operations",
    ],
    "economic": [
        "Currency volatility in {region} impacting procurement costs",
        "Inflation surge drives raw material prices to 10-year high",
        "Major supplier {company} files for bankruptcy protection",
        "Credit crunch affecting smaller suppliers in {region}",
        "Fuel price spike increasing logistics costs by {percent}%",
    ],
    "transportation": [
        "Port congestion at {port} reaching critical levels, 50+ vessels waiting",
        "Rail strike in {country} disrupts inland logistics network",
        "Shipping container shortage continues, rates up {percent}%",
        "Major highway closure in {region} rerouting truck freight",
        "Air freight capacity reduced due to {reason}",
    ],
    "labor_strike": [
        "Workers at {company} announce strike over wage disputes",
        "Port workers union threatens work stoppage at {port}",
        "Manufacturing strike in {country} affects {product} production",
        "Logistics workers demand better conditions, slowdowns reported",
    ],
    "cyber_attack": [
        "Ransomware attack on {company} disrupts operations globally",
        "Cyber incident at major port operator causing delays",
        "Supply chain software provider hit by security breach",
        "Logistics company {company} systems offline after attack",
    ],
}

COMPANIES = ["Acme Corp", "GlobalTech", "MegaSupply", "TradeCo", "PrimeParts", "UniSource", "AlphaLogistics"]
PORTS = ["Shanghai", "Singapore", "Rotterdam", "Los Angeles", "Hamburg", "Shenzhen", "Mumbai JNPT", "Chennai", "Mundra", "Visakhapatnam"]
PRODUCTS = ["semiconductors", "automotive parts", "pharmaceuticals", "consumer electronics", "raw materials", "chemicals"]
COUNTRIES = ["China", "Japan", "Germany", "India", "Vietnam", "Taiwan", "South Korea", "Mexico"]
LOCATIONS = ["Taiwan", "Guangdong Province", "Bavaria", "California", "Tokyo metropolitan area", "Yangtze Delta", "Gujarat", "Tamil Nadu", "Maharashtra", "Delhi NCR"]


def generate_news_headline(disruption_type: str) -> tuple[str, str]:
    """Generate a realistic news headline based on disruption type"""
    templates = NEWS_TEMPLATES.get(disruption_type, NEWS_TEMPLATES["economic"])
    template = random.choice(templates)
    
    headline = template.format(
        name=f"Hurricane {''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=1))}-{random.randint(1, 12)}",
        region=random.choice([r["name"] for r in REGIONS]),
        magnitude=round(random.uniform(5.5, 8.0), 1),
        location=random.choice(LOCATIONS),
        product=random.choice(PRODUCTS),
        country=random.choice(COUNTRIES),
        country1=random.choice(COUNTRIES),
        country2=random.choice([c for c in COUNTRIES if c != random.choice(COUNTRIES)]),
        company=random.choice(COMPANIES),
        port=random.choice(PORTS),
        percent=random.randint(15, 150),
        reason="airline capacity cuts",
    )
    
    # Generate description
    descriptions = [
        f"Industry analysts warn of significant supply chain impact. Companies advised to review contingency plans.",
        f"Market response expected as logistics networks adapt to changing conditions.",
        f"Supply chain experts monitoring situation closely. Alternative routes being evaluated.",
        f"Procurement teams across industries assessing potential impact on Q{random.randint(1,4)} deliveries.",
    ]
    
    return headline, random.choice(descriptions)


def generate_mock_news(count: int = 20) -> List[NewsArticle]:
    """Generate mock news articles for demo"""
    articles = []
    disruption_types = list(DisruptionType)
    
    for i in range(count):
        d_type = random.choice(disruption_types)
        headline, description = generate_news_headline(d_type.value)
        
        # Generate realistic sentiment (negative news more common for disruptions)
        sentiment = random.gauss(-0.3, 0.4)
        sentiment = max(-1.0, min(1.0, sentiment))
        
        region = random.choice(REGIONS)
        
        articles.append(NewsArticle(
            id=str(uuid.uuid4()),
            title=headline,
            description=description,
            content=f"{description} {headline} Additional analysis continues...",
            source=random.choice(["Reuters", "Bloomberg", "WSJ", "Financial Times", "Supply Chain Dive", "Logistics News"]),
            url=f"https://example.com/news/{uuid.uuid4().hex[:8]}",
            published_at=datetime.utcnow() - timedelta(hours=random.randint(0, 72)),
            sentiment_score=round(sentiment, 3),
            relevance_score=round(random.uniform(0.6, 1.0), 3),
            entities=[random.choice(COMPANIES), random.choice(PRODUCTS)],
            disruption_type=d_type,
            region=region["name"],
        ))
    
    return sorted(articles, key=lambda x: x.published_at, reverse=True)


def generate_predictions(days_ahead: int = 30) -> List[Prediction]:
    """Generate AI predictions for supply chain disruptions"""
    predictions = []
    
    for i in range(days_ahead):
        # Probability of prediction decreases further in future
        if random.random() > 0.3 + (i * 0.02):  # More predictions near-term
            continue
            
        prediction_date = datetime.utcnow() + timedelta(days=i)
        risk_score = random.betavariate(2, 5)  # Skewed toward lower risks
        
        # Determine risk level
        if risk_score >= 0.85:
            risk_level = RiskLevel.CRITICAL
        elif risk_score >= 0.7:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 0.4:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
            
        d_type = random.choice(list(DisruptionType))
        region = random.choice(REGIONS)
        
        predictions.append(Prediction(
            id=str(uuid.uuid4()),
            prediction_date=prediction_date,
            risk_score=round(risk_score, 3),
            risk_level=risk_level,
            confidence=round(random.uniform(0.65, 0.95), 3),
            disruption_type=d_type,
            region=region["name"],
            affected_categories=random.sample(SUPPLY_CHAIN_CATEGORIES, k=random.randint(1, 3)),
            contributing_factors=[
                f"News sentiment trending negative in {region['name']}",
                f"Historical pattern match for {d_type.value.replace('_', ' ')} events",
                f"Supplier concentration risk elevated",
            ][:random.randint(1, 3)],
            recommended_actions=[
                "Activate alternative supplier contingency plans",
                "Increase safety stock for critical components",
                "Monitor situation and prepare communication to stakeholders",
                "Review force majeure clauses with affected suppliers",
            ][:random.randint(1, 3)],
        ))
    
    return sorted(predictions, key=lambda x: x.risk_score, reverse=True)


def generate_alerts() -> List[Alert]:
    """Generate active alerts based on predictions"""
    alerts = []
    
    alert_scenarios = [
        {
            "title": "Critical: Semiconductor Supply Risk - Asia Pacific",
            "message": "AI models predict 87% probability of significant semiconductor supply disruption in the next 14 days due to geopolitical tensions and manufacturing capacity constraints.",
            "risk_level": RiskLevel.CRITICAL,
            "disruption_type": DisruptionType.GEOPOLITICAL,
            "region": "Asia Pacific",
        },
        {
            "title": "High: Port Congestion Alert - Europe",
            "message": "Rotterdam and Hamburg ports experiencing severe congestion. Container delays expected to impact logistics for 3-4 weeks.",
            "risk_level": RiskLevel.HIGH,
            "disruption_type": DisruptionType.TRANSPORTATION,
            "region": "Europe",
        },
        {
            "title": "Medium: Raw Material Price Volatility",
            "message": "Commodity prices showing unusual volatility. Procurement teams advised to review hedging strategies.",
            "risk_level": RiskLevel.MEDIUM,
            "disruption_type": DisruptionType.ECONOMIC,
            "region": "North America",
        },
        {
            "title": "High: Weather Alert - Latin America",
            "message": "La Niña conditions strengthening. Agricultural and mining supply chains at elevated risk.",
            "risk_level": RiskLevel.HIGH,
            "disruption_type": DisruptionType.NATURAL_DISASTER,
            "region": "Latin America",
        },
        {
            "title": "Medium: Supplier Financial Health Warning",
            "message": "3 tier-2 suppliers showing signs of financial distress. Alternative sourcing recommended.",
            "risk_level": RiskLevel.MEDIUM,
            "disruption_type": DisruptionType.SUPPLIER_FAILURE,
            "region": "Europe",
        },
    ]
    
    for i, scenario in enumerate(alert_scenarios):
        alerts.append(Alert(
            id=str(uuid.uuid4()),
            created_at=datetime.utcnow() - timedelta(hours=random.randint(0, 24)),
            title=scenario["title"],
            message=scenario["message"],
            risk_level=scenario["risk_level"],
            disruption_type=scenario["disruption_type"],
            region=scenario["region"],
            is_read=i > 2,  # First 3 unread
            is_acknowledged=i > 3,  # First 4 unacknowledged
        ))
    
    return alerts


def generate_region_risks() -> List[RegionRisk]:
    """Generate risk data for each geographic region"""
    region_risks = []
    
    for region in REGIONS:
        risk_score = random.betavariate(2, 5) * 1.5  # Slightly elevated
        risk_score = min(1.0, risk_score)
        
        if risk_score >= 0.85:
            risk_level = RiskLevel.CRITICAL
        elif risk_score >= 0.7:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 0.4:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
            
        top_risks = random.sample([
            "Port congestion",
            "Semiconductor shortage", 
            "Currency volatility",
            "Labor disputes",
            "Regulatory changes",
            "Weather events",
            "Supplier concentration",
        ], k=random.randint(2, 4))
        
        region_risks.append(RegionRisk(
            region_code=region["code"],
            region_name=region["name"],
            lat=region["lat"],
            lng=region["lng"],
            risk_score=round(risk_score, 3),
            risk_level=risk_level,
            active_alerts=random.randint(0, 5),
            top_risks=top_risks,
        ))
    
    return region_risks


def generate_risk_metrics() -> List[RiskMetric]:
    """Generate risk metrics for each supply chain category"""
    metrics = []
    
    for category in SUPPLY_CHAIN_CATEGORIES:
        current = random.betavariate(3, 5)
        previous = current + random.gauss(0, 0.1)
        previous = max(0, min(1, previous))
        
        change = current - previous
        if abs(change) < 0.02:
            trend = "stable"
        elif change > 0:
            trend = "up"
        else:
            trend = "down"
            
        metrics.append(RiskMetric(
            category=category,
            current_score=round(current, 3),
            previous_score=round(previous, 3),
            trend=trend,
            change_percent=round(change * 100, 1),
        ))
    
    return sorted(metrics, key=lambda x: x.current_score, reverse=True)


def generate_suppliers(count: int = 15) -> List[Supplier]:
    """Generate supplier profiles with risk assessments"""
    suppliers = []
    
    supplier_names = [
        "Taiwan Semiconductor Manufacturing", "Samsung Electronics", "Intel Corporation",
        "Foxconn Technology", "BASF Chemical", "Bosch Automotive", "Continental AG",
        "LG Display", "Micron Technology", "SK Hynix", "Infineon Technologies",
        "Tata Motors", "Reliance Industries", "Mahindra & Mahindra", "Wipro Limited",
        "Adani Ports & SEZ", "Infosys BPM", "Larsen & Toubro", "Bharat Electronics",
    ]
    
    for i, name in enumerate(supplier_names[:count]):
        risk_score = random.betavariate(2, 4)
        
        suppliers.append(Supplier(
            id=str(uuid.uuid4()),
            name=name,
            region=random.choice([r["name"] for r in REGIONS]),
            categories=random.sample(SUPPLY_CHAIN_CATEGORIES, k=random.randint(1, 3)),
            risk_score=round(risk_score, 3),
            last_assessed=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
            tier=random.choices([1, 2, 3], weights=[0.3, 0.5, 0.2])[0],
            is_critical=risk_score > 0.6 or random.random() > 0.7,
        ))
    
    return sorted(suppliers, key=lambda x: x.risk_score, reverse=True)


def generate_dashboard_summary() -> DashboardSummary:
    """Generate executive dashboard summary"""
    alerts = generate_alerts()
    
    overall_risk = random.betavariate(3, 4)
    
    if overall_risk >= 0.85:
        risk_level = RiskLevel.CRITICAL
    elif overall_risk >= 0.7:
        risk_level = RiskLevel.HIGH
    elif overall_risk >= 0.4:
        risk_level = RiskLevel.MEDIUM
    else:
        risk_level = RiskLevel.LOW
    
    return DashboardSummary(
        overall_risk_score=round(overall_risk, 3),
        overall_risk_level=risk_level,
        risk_trend=random.choice(["up", "down", "stable"]),
        total_active_alerts=len(alerts),
        critical_alerts=len([a for a in alerts if a.risk_level == RiskLevel.CRITICAL]),
        high_alerts=len([a for a in alerts if a.risk_level == RiskLevel.HIGH]),
        regions_at_risk=random.randint(2, 4),
        predictions_accuracy=round(random.uniform(0.82, 0.94), 3),
        last_updated=datetime.utcnow(),
    )


def generate_time_series_data(days: int = 90) -> List[Dict[str, Any]]:
    """Generate time series data for trend charts"""
    data = []
    base_risk = 0.45
    
    for i in range(days):
        date = datetime.utcnow() - timedelta(days=days - i - 1)
        
        # Add some realistic patterns
        seasonal_factor = 0.1 * math.sin(2 * math.pi * i / 30)  # Monthly seasonality
        trend_factor = 0.001 * i  # Slight upward trend
        random_factor = random.gauss(0, 0.05)
        
        risk = base_risk + seasonal_factor + trend_factor + random_factor
        risk = max(0, min(1, risk))
        
        data.append({
            "date": date.strftime("%Y-%m-%d"),
            "overall_risk": round(risk, 3),
            "logistics_risk": round(risk + random.gauss(0, 0.05), 3),
            "supplier_risk": round(risk + random.gauss(0.05, 0.05), 3),
            "geopolitical_risk": round(risk + random.gauss(-0.05, 0.05), 3),
            "news_volume": random.randint(50, 200),
            "sentiment_avg": round(random.gauss(-0.1, 0.3), 3),
        })
    
    return data


# Singleton data store with SQLite persistence
class DataStore:
    """Data store with SQLite persistence — loads from DB, falls back to generation"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        # Try loading from database first
        if not self.load_from_db():
            # No data in DB — generate fresh data and save it
            self._generate_fresh_data()
            self.save_to_db()
        self._initialized = True
    
    def _generate_fresh_data(self):
        """Generate all mock data"""
        self.news = generate_mock_news(25)
        self.predictions = generate_predictions(30)
        self.alerts = generate_alerts()
        self.region_risks = generate_region_risks()
        self.risk_metrics = generate_risk_metrics()
        self.suppliers = generate_suppliers(15)
        self.dashboard_summary = generate_dashboard_summary()
        self.time_series = generate_time_series_data(90)
        self.last_refreshed = datetime.utcnow()

    def refresh_data(self):
        """Refresh all data and persist to database"""
        self._generate_fresh_data()
        self.save_to_db()

    def save_to_db(self):
        """Save all current data to MongoDB"""
        try:
            from app.core.database import get_db
            from app.models.db_models import pydantic_to_doc
            
            db = get_db()
            
            # Clear and re-insert all collections
            collections_data = {
                "news_articles": [pydantic_to_doc(a) for a in self.news],
                "predictions": [pydantic_to_doc(p) for p in self.predictions],
                "alerts": [pydantic_to_doc(a) for a in self.alerts],
                "suppliers": [pydantic_to_doc(s) for s in self.suppliers],
                "region_risks": [pydantic_to_doc(r) for r in self.region_risks],
                "risk_metrics": [pydantic_to_doc(r) for r in self.risk_metrics],
                "time_series": self.time_series,
            }
            
            for collection_name, docs in collections_data.items():
                db[collection_name].delete_many({})
                if docs:
                    db[collection_name].insert_many(docs)
            
            # Dashboard summary — single document
            summary_doc = pydantic_to_doc(self.dashboard_summary)
            db.dashboard_summary.delete_many({})
            db.dashboard_summary.insert_one(summary_doc)
            
            logger.info("💾 Data saved to MongoDB")
        except Exception as e:
            logger.error(f"Failed to save to MongoDB: {e}")

    def load_from_db(self) -> bool:
        """Load data from MongoDB. Returns True if data was loaded."""
        try:
            from app.core.database import get_db
            from app.models.db_models import (
                doc_to_news, doc_to_prediction, doc_to_alert,
                doc_to_supplier, doc_to_region_risk, doc_to_risk_metric,
                doc_to_dashboard_summary,
            )
            
            db = get_db()
            
            # Check if any data exists
            if db.dashboard_summary.count_documents({}) == 0:
                return False
            
            self.news = [doc_to_news(d) for d in db.news_articles.find()]
            self.predictions = [doc_to_prediction(d) for d in db.predictions.find()]
            self.alerts = [doc_to_alert(d) for d in db.alerts.find()]
            self.suppliers = [doc_to_supplier(d) for d in db.suppliers.find()]
            self.region_risks = [doc_to_region_risk(d) for d in db.region_risks.find()]
            self.risk_metrics = [doc_to_risk_metric(d) for d in db.risk_metrics.find()]
            
            summary_doc = db.dashboard_summary.find_one()
            self.dashboard_summary = doc_to_dashboard_summary(summary_doc)
            
            self.time_series = list(db.time_series.find({}, {"_id": 0}))
            
            self.last_refreshed = datetime.utcnow()
            logger.info(f"📂 Loaded from MongoDB: {len(self.news)} news, {len(self.suppliers)} suppliers, {len(self.alerts)} alerts")
            return True
        except Exception as e:
            logger.error(f"Failed to load from MongoDB: {e}")
            return False


def get_data_store() -> DataStore:
    """Get the singleton data store instance"""
    return DataStore()

