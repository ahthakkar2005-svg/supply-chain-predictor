"""API routes package"""
from .dashboard import router as dashboard_router
from .predictions import router as predictions_router
from .websocket import router as websocket_router

__all__ = ["dashboard_router", "predictions_router", "websocket_router"]
