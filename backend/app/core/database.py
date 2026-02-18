"""
Database configuration — MongoDB with PyMongo
"""
import logging
from pymongo import MongoClient
from pymongo.database import Database

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Singleton connection
_client: MongoClient | None = None
_db: Database | None = None

DB_NAME = "supply_chain_predictor"


def get_mongo_client() -> MongoClient:
    """Get or create MongoDB client"""
    global _client
    if _client is None:
        settings = get_settings()
        mongo_url = settings.MONGODB_URL
        _client = MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
    return _client


def get_db() -> Database:
    """Get the MongoDB database instance"""
    global _db
    if _db is None:
        client = get_mongo_client()
        _db = client[DB_NAME]
    return _db


def init_db():
    """Initialize MongoDB — ensure connection and create indexes"""
    try:
        db = get_db()
        # Ping to verify connection
        db.client.admin.command("ping")
        
        # Create indexes for common queries
        db.news_articles.create_index("region")
        db.predictions.create_index("region")
        db.alerts.create_index("risk_level")
        db.suppliers.create_index("region")
        db.region_risks.create_index("region_code", unique=True)
        db.risk_metrics.create_index("category", unique=True)
        
        logger.info(f"📦 MongoDB connected: {DB_NAME}")
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        logger.warning("⚠️ Falling back to in-memory data only")


def close_db():
    """Close MongoDB connection"""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("🔌 MongoDB connection closed")
