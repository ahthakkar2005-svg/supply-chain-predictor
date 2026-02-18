"""Services module - Business logic and data processing"""
from .data_simulator import get_data_store, DataStore
from .connection_manager import get_connection_manager, ConnectionManager
from .news_service import get_news_service, NewsService
from .weather_service import get_weather_service, WeatherService
from .realtime_engine import get_realtime_engine, RealtimeEngine

__all__ = [
    "get_data_store", "DataStore",
    "get_connection_manager", "ConnectionManager",
    "get_news_service", "NewsService",
    "get_weather_service", "WeatherService",
    "get_realtime_engine", "RealtimeEngine",
]
