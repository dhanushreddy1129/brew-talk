"""WebSocket event hub for real-time broadcasting."""

import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class EventHub:
    """Manages WebSocket connections grouped by channel and broadcasts events."""

    def __init__(self) -> None:
        self.connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel: str = "general") -> None:
        """Accept and register a WebSocket connection on a channel."""
        await websocket.accept()
        self.connections.setdefault(channel, []).append(websocket)

    def disconnect(self, websocket: WebSocket, channel: str = "general") -> None:
        """Remove a WebSocket connection from a channel."""
        if channel in self.connections:
            try:
                self.connections[channel].remove(websocket)
            except ValueError:
                pass
            # Clean up empty channel lists
            if not self.connections[channel]:
                del self.connections[channel]

    async def broadcast(
        self,
        event_type: str,
        data: dict[str, Any],
        channel: str = "general",
    ) -> None:
        """
        Send {"type": event_type, "data": data} to all connections on a channel.
        Silently removes dead connections.
        """
        if channel not in self.connections:
            return

        message = json.dumps({"type": event_type, "data": data})
        dead: list[WebSocket] = []

        for ws in self.connections[channel]:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)

        # Remove dead connections
        for ws in dead:
            try:
                self.connections[channel].remove(ws)
            except ValueError:
                pass

        if channel in self.connections and not self.connections[channel]:
            del self.connections[channel]


# Singleton instance
event_hub = EventHub()
