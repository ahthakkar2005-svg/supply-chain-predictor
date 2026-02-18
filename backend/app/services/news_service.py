"""
News Service - Fetches real supply chain news from NewsAPI
Falls back to simulated data when API key is not configured
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional
import random

import httpx

from app.core.config import get_settings
from app.models import NewsArticle, DisruptionType

logger = logging.getLogger(__name__)

# Supply chain related search queries
SUPPLY_CHAIN_QUERIES = [
    "supply chain disruption",
    "shipping port congestion",
    "semiconductor shortage",
    "trade tariff",
    "logistics delay",
    "manufacturing shutdown",
    "raw material shortage",
]

# Keywords to disruption type mapping
DISRUPTION_KEYWORDS = {
    DisruptionType.NATURAL_DISASTER: ["typhoon", "hurricane", "earthquake", "flood", "wildfire", "storm", "drought", "tsunami"],
    DisruptionType.GEOPOLITICAL: ["tariff", "sanction", "trade war", "embargo", "political", "border", "tension"],
    DisruptionType.ECONOMIC: ["inflation", "recession", "bankruptcy", "currency", "price surge", "cost", "credit"],
    DisruptionType.TRANSPORTATION: ["port", "shipping", "freight", "congestion", "logistics", "container", "rail"],
    DisruptionType.LABOR_STRIKE: ["strike", "labor", "workers", "union", "wage", "protest"],
    DisruptionType.CYBER_ATTACK: ["cyber", "ransomware", "hack", "breach", "security"],
    DisruptionType.PANDEMIC: ["pandemic", "covid", "outbreak", "virus", "quarantine"],
    DisruptionType.REGULATORY: ["regulation", "compliance", "ban", "policy", "law"],
    DisruptionType.SUPPLIER_FAILURE: ["supplier", "bankruptcy", "default", "insolvency"],
}

# Region detection keywords
REGION_KEYWORDS = {
    "Asia Pacific": ["china", "japan", "taiwan", "korea", "vietnam", "asia", "pacific", "semiconductor", "foxconn", "tsmc"],
    "South Asia (India)": ["india", "mumbai", "delhi", "chennai", "kolkata", "gujarat", "bangalore", "hyderabad", "pune", "jnpt", "mundra", "visakhapatnam", "tata", "reliance", "adani", "infosys", "wipro", "mahindra"],
    "Europe": ["europe", "eu", "germany", "france", "uk", "rotterdam", "hamburg", "brexit"],
    "North America": ["us", "usa", "america", "canada", "mexico", "california", "texas"],
    "Latin America": ["brazil", "argentina", "chile", "latin america", "south america"],
    "Middle East & Africa": ["middle east", "africa", "saudi", "uae", "nigeria", "suez"],
}


def _simple_sentiment(text: str) -> float:
    """Simple keyword-based sentiment scoring"""
    if not text:
        return 0.0

    text_lower = text.lower()

    negative_words = [
        "disruption", "shortage", "delay", "crisis", "risk", "threat", "decline",
        "crash", "collapse", "failure", "shutdown", "strike", "attack", "surge",
        "congestion", "embargo", "sanction", "tariff", "bankrupt", "loss",
        "warning", "critical", "severe", "damage", "halt", "suspend",
    ]
    positive_words = [
        "recovery", "growth", "improvement", "expansion", "investment", "stable",
        "increase", "profit", "deal", "agreement", "resolve", "boost", "strong",
        "innovation", "partnership", "milestone", "success", "launch",
    ]

    neg_count = sum(1 for w in negative_words if w in text_lower)
    pos_count = sum(1 for w in positive_words if w in text_lower)

    total = neg_count + pos_count
    if total == 0:
        return 0.0

    score = (pos_count - neg_count) / total
    return round(max(-1.0, min(1.0, score)), 3)


def _detect_disruption_type(text: str) -> Optional[DisruptionType]:
    """Detect disruption type from text content"""
    text_lower = text.lower()
    best_match = None
    best_count = 0

    for d_type, keywords in DISRUPTION_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw in text_lower)
        if count > best_count:
            best_count = count
            best_match = d_type

    return best_match


def _detect_region(text: str) -> Optional[str]:
    """Detect geographic region from text content"""
    text_lower = text.lower()
    best_region = None
    best_count = 0

    for region, keywords in REGION_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw in text_lower)
        if count > best_count:
            best_count = count
            best_region = region

    return best_region


class NewsService:
    """Fetches real supply chain news from NewsAPI"""

    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.NEWS_API_KEY
        self.base_url = "https://newsapi.org/v2"
        self._last_articles: List[NewsArticle] = []
        self._last_fetch: Optional[datetime] = None

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def fetch_news(self, max_articles: int = 20) -> List[NewsArticle]:
        """Fetch real news from NewsAPI, falls back to mock on failure"""
        if not self.is_configured:
            logger.info("NewsAPI key not set, using simulated news")
            return self._generate_mock_news(max_articles)

        try:
            articles = await self._fetch_from_api(max_articles)
            if articles:
                self._last_articles = articles
                self._last_fetch = datetime.utcnow()
                logger.info(f"Fetched {len(articles)} real news articles from NewsAPI")
                return articles
        except Exception as e:
            logger.warning(f"NewsAPI fetch failed: {e}, using mock data")

        return self._generate_mock_news(max_articles)

    async def _fetch_from_api(self, max_articles: int) -> List[NewsArticle]:
        """Fetch articles from NewsAPI"""
        query = random.choice(SUPPLY_CHAIN_QUERIES)
        params = {
            "q": query,
            "apiKey": self.api_key,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": min(max_articles, 100),
            "from": (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d"),
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(f"{self.base_url}/everything", params=params)
            response.raise_for_status()
            data = response.json()

        articles = []
        for item in data.get("articles", [])[:max_articles]:
            title = item.get("title", "")
            description = item.get("description", "")
            full_text = f"{title} {description}"

            if not title or title == "[Removed]":
                continue

            sentiment = _simple_sentiment(full_text)
            disruption_type = _detect_disruption_type(full_text)
            region = _detect_region(full_text)

            try:
                published = datetime.fromisoformat(item["publishedAt"].replace("Z", "+00:00"))
            except (KeyError, ValueError):
                published = datetime.utcnow()

            articles.append(NewsArticle(
                id=str(uuid.uuid4()),
                title=title,
                description=description,
                content=item.get("content"),
                source=item.get("source", {}).get("name", "Unknown"),
                url=item.get("url", ""),
                published_at=published,
                sentiment_score=sentiment,
                relevance_score=round(random.uniform(0.6, 1.0), 3),
                entities=[],
                disruption_type=disruption_type,
                region=region,
            ))

        return sorted(articles, key=lambda x: x.published_at, reverse=True)

    def _generate_mock_news(self, count: int = 20) -> List[NewsArticle]:
        """Generate simulated news for when API is unavailable"""
        from app.services.data_simulator import generate_mock_news
        return generate_mock_news(count)

    def get_new_articles(self, since: datetime) -> List[NewsArticle]:
        """Get articles published since a given timestamp"""
        return [a for a in self._last_articles if a.published_at > since]


# Singleton
_news_service: Optional[NewsService] = None


def get_news_service() -> NewsService:
    global _news_service
    if _news_service is None:
        _news_service = NewsService()
    return _news_service
