"""
Supply Chain Disruption Predictor - FastAPI Backend
Main application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.api import dashboard_router, predictions_router, websocket_router
from app.core.config import get_settings
from app.services import get_data_store
from app.services.realtime_engine import get_realtime_engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 Starting Supply Chain Disruption Predictor API...")
    settings = get_settings()
    logger.info(f"📊 App: {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Initialize MongoDB connections
    from app.core.database import init_db, init_async_db, close_db, close_async_db
    init_db()
    await init_async_db()
    
    # Start real-time engine
    engine = get_realtime_engine()
    await engine.start()
    logger.info("⚡ Real-time engine started")
    
    yield
    
    # Shutdown
    engine = get_realtime_engine()
    await engine.stop()
    close_db()
    await close_async_db()
    logger.info("👋 Shutting down Supply Chain Disruption Predictor API...")


# Initialize FastAPI app
settings = get_settings()
app = FastAPI(
    title=settings.APP_NAME,
    description="""
    🔮 **AI-Powered Supply Chain Disruption Prediction System**
    
    Analyze unstructured data (news, social media, market signals) to predict 
    supply chain disruptions before they occur.
    
    ## Features
    
    * 📰 **Real-time News Analysis** - NLP-powered sentiment and entity extraction
    * 🤖 **AI Predictions** - LSTM & Prophet models for disruption forecasting
    * 🗺️ **Geographic Risk Mapping** - Regional risk visualization
    * 🚨 **Smart Alerts** - Proactive notifications with prioritization
    * 📊 **Executive Dashboard** - KPIs and trend analysis
    * ⚡ **WebSocket Real-time Updates** - Live data streaming
    
    ## API Sections
    
    * `/api/dashboard` - Dashboard data (summary, regions, metrics, alerts)
    * `/api/predictions` - AI predictions and risk analysis
    * `/ws` - WebSocket endpoint for real-time updates
    """,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from fastapi import Depends
from app.auth.dependencies import get_current_user
from app.auth.router import router as auth_router

app.include_router(auth_router)
app.include_router(
    dashboard_router,
    dependencies=[Depends(get_current_user)]
)
app.include_router(
    predictions_router,
    dependencies=[Depends(get_current_user)]
)
app.include_router(websocket_router)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - API information"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "realtime": True,
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "dashboard": "/api/dashboard",
            "predictions": "/api/predictions",
            "websocket": "/ws"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    from app.services.connection_manager import get_connection_manager
    manager = get_connection_manager()
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "websocket_connections": manager.connection_count,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

