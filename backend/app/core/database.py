"""
Database configuration — MongoDB with Motor (async) driver
FIX 4: Replaced sync PyMongo with async Motor, added connection pooling and lifespan events.
Also retains sync PyMongo access for auth dependencies that run in sync context.
"""
import logging
from typing import Optional

from pymongo import MongoClient
from pymongo.database import Database

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# ---------- Sync PyMongo (for auth dependencies, quick lookups) ----------
_client: Optional[MongoClient] = None
_db: Optional[Database] = None


def get_mongo_client() -> MongoClient:
    """Get or create sync MongoDB client."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = MongoClient(
            settings.MONGODB_URL,
            serverSelectionTimeoutMS=5000,
            maxPoolSize=50,
            minPoolSize=5,
        )
    return _client


def get_db() -> Optional[Database]:
    """Get the sync MongoDB database instance. Returns None if connection fails."""
    global _db
    if _db is None:
        try:
            client = get_mongo_client()
            settings = get_settings()
            _db = client[settings.MONGODB_DB_NAME]
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return None
    return _db


def init_db():
    """Initialise MongoDB — ensure connection and create indexes."""
    try:
        db = get_db()
        if db is None:
            raise ConnectionError("Could not get database handle")

        db.client.admin.command("ping")

        # Collection indexes
        db.news_articles.create_index("region")
        db.news_articles.create_index("published_at")
        db.news_articles.create_index("dedup_hash", unique=True, sparse=True)
        db.predictions.create_index("region")
        db.predictions.create_index("created_at")
        db.predictions.create_index("tenant_id")
        db.alerts.create_index("risk_level")
        db.alerts.create_index("tenant_id")
        db.alerts.create_index("created_at")
        db.suppliers.create_index("region")
        db.suppliers.create_index("tenant_id")
        db.region_risks.create_index("region_code", unique=True)
        db.risk_metrics.create_index("category", unique=True)

        # Auth indexes
        db.users.create_index("email", unique=True)
        db.users.create_index("tenant_id")
        db.token_blacklist.create_index("jti", unique=True)
        db.token_blacklist.create_index("expires_at", expireAfterSeconds=0)  # TTL

        # Audit log indexes
        db.audit_logs.create_index("tenant_id")
        db.audit_logs.create_index("user_id")
        db.audit_logs.create_index("timestamp")
        db.audit_logs.create_index("action")

        # Risk model config
        db.risk_model_config.create_index("tenant_id", unique=True)

        logger.info(f"📦 MongoDB connected: {get_settings().MONGODB_DB_NAME}")

    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        logger.warning("⚠️ Falling back to in-memory data only")


def close_db():
    """Close MongoDB connection."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("🔌 MongoDB connection closed")


# ---------- Async Motor (for route handlers, real-time engine) ----------
_async_client = None
_async_db = None


async def init_async_db():
    """Initialise async Motor client for use in route handlers."""
    global _async_client, _async_db
    try:
        from motor.motor_asyncio import AsyncIOMotorClient

        settings = get_settings()
        client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            maxPoolSize=50,
            minPoolSize=5,
            serverSelectionTimeoutMS=2000,
        )
        await client.admin.command("ping")
        _async_client = client
        _async_db = _async_client[settings.MONGODB_DB_NAME]
        logger.info("⚡ Async Motor client connected")

    except Exception as e:
        logger.warning(f"⚠️ Async Motor connection failed: {e}. Using in-memory DataStore fallback.")
        _async_client = None
        _async_db = None


async def close_async_db():
    """Close async Motor client."""
    global _async_client, _async_db
    if _async_client:
        _async_client.close()
        _async_client = None
        _async_db = None
        logger.info("🔌 Async Motor connection closed")


def get_async_db():
    """Get async Motor database instance."""
    return _async_db


# ---------- Collection helpers ----------

def get_collection(name: str):
    """Get a sync collection by name."""
    db = get_db()
    return db[name] if db else None


async def get_async_collection(name: str):
    """Get an async collection by name."""
    db = get_async_db()
    if db is None:
        return None
    return db[name]
