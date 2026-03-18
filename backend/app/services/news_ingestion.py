"""
News Ingestion Service — FIX 5 / FIX 13
Handles NewsAPI + GDELT ingestion with deduplication.
"""
import hashlib
import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from app.core.config import get_settings
from app.models.db_models import NewsArticle, DisruptionType
import httpx

logger = logging.getLogger(__name__)


class NewsIngestionService:
    """
    Ingests news from NewsAPI and GDELT, deduplicates by content hash,
    and stores in MongoDB with credibility score and supply-chain relevance tag.
    """

    def __init__(self):
        self.settings = get_settings()

    def _compute_dedup_hash(self, title: str, source: str) -> str:
        """Create a dedup hash from title + source."""
        content = f"{title.strip().lower()}|{source.strip().lower()}"
        return hashlib.sha256(content.encode()).hexdigest()

    async def ingest_from_newsapi(self, max_articles: int = 20) -> List[dict]:
        """Fetch articles from NewsAPI and store in MongoDB."""
        import httpx
        from app.services.news_service import (
            SUPPLY_CHAIN_QUERIES, _simple_sentiment,
            _detect_disruption_type, _detect_region,
        )

        api_key = self.settings.NEWS_API_KEY
        if api_key is None:
            logger.info("NewsAPI key not configured — skipping ingestion")
            return []

        key_value = api_key.get_secret_value() if hasattr(api_key, "get_secret_value") else str(api_key)
        if not key_value or key_value.startswith("your_"):
            logger.info("NewsAPI key is placeholder — skipping ingestion")
            return []

        articles_stored = []
        import random
        query = random.choice(SUPPLY_CHAIN_QUERIES)

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                params = {
                    "q": query,
                    "apiKey": key_value,
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": min(max_articles, 100),
                    "from": (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d"),
                }
                response = await client.get("https://newsapi.org/v2/everything", params=params)
                response.raise_for_status()
                data = response.json()

            from app.core.database import get_async_collection
            db_news = await get_async_collection("news_articles")

            for item in data.get("articles", []):
                title = item.get("title", "")
                if not title or title == "[Removed]":
                    continue

                source_name = item.get("source", {}).get("name", "Unknown")
                dedup_hash = self._compute_dedup_hash(title, source_name)

                # Skip duplicates
                existing = await db_news.find_one({"dedup_hash": dedup_hash})
                if existing:
                    continue

                description = item.get("description", "")
                full_text = f"{title} {description}"
                sentiment = _simple_sentiment(full_text)
                disruption_type = _detect_disruption_type(full_text)
                region = _detect_region(full_text)

                try:
                    published = datetime.fromisoformat(
                        item["publishedAt"].replace("Z", "+00:00")
                    )
                except (KeyError, ValueError):
                    published = datetime.utcnow()

                doc = {
                    "_id": str(uuid.uuid4()),
                    "title": title,
                    "description": description,
                    "content": item.get("content"),
                    "source": source_name,
                    "url": item.get("url", ""),
                    "published_at": published,
                    "sentiment_score": sentiment,
                    "relevance_score": self._compute_relevance(full_text),
                    "entities": [],
                    "disruption_type": disruption_type.value if disruption_type else None,
                    "region": region,
                    "dedup_hash": dedup_hash,
                    "credibility_score": self._source_credibility(source_name),
                    "ingested_at": datetime.utcnow(),
                }

                try:
                    await db_news.insert_one(doc)
                    articles_stored.append(doc)
                except Exception as e:
                    logger.debug(f"Duplicate insert skipped: {e}")

            logger.info(f"Ingested {len(articles_stored)} new articles from NewsAPI")

        except Exception as e:
            logger.error(f"NewsAPI ingestion failed: {e}")

        return articles_stored

    def _compute_relevance(self, text: str) -> float:
        """Score how relevant text is to supply chain topics."""
        keywords = [
            "supply chain", "logistics", "shipping", "port", "semiconductor",
            "manufacturing", "supplier", "freight", "tariff", "disruption",
            "shortage", "inventory", "warehouse", "procurement",
        ]
        text_lower = text.lower()
        hits = sum(1 for kw in keywords if kw in text_lower)
        return round(min(1.0, 0.3 + hits * 0.1), 3)

    def _source_credibility(self, source: str) -> float:
        """Assign credibility score based on source reputation."""
        high_cred = {"Reuters", "Bloomberg", "Financial Times", "WSJ", "AP News", "BBC"}
        mid_cred = {"CNBC", "Supply Chain Dive", "The Guardian", "Forbes"}
        if source in high_cred:
            return 0.95
        if source in mid_cred:
            return 0.80
        return 0.60
