"""
WebSocket Connection Manager
Manages active WebSocket connections and broadcasts messages to all clients
"""
import logging
import json
from typing import Set, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_json(self, websocket: WebSocket, data: Any):
        """Send JSON data to a specific client"""
        try:
            await websocket.send_json(data)
        except Exception as e:
            logger.warning(f"Failed to send to client: {e}")
            self.disconnect(websocket)

    async def broadcast(self, event_type: str, data: Any):
        """Broadcast an event to all connected clients"""
        if not self.active_connections:
            return

        message = {
            "event": event_type,
            "data": data,
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        }

        disconnected = set()
        for connection in self.active_connections.copy():
            try:
                await connection.send_text(json.dumps(message, default=str))
            except Exception:
                disconnected.add(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

        if disconnected:
            logger.info(f"Cleaned up {len(disconnected)} stale connections")

    @property
    def connection_count(self) -> int:
        return len(self.active_connections)


# Singleton instance
_manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    return _manager
