"""WebSocket endpoint for real-time event streaming."""

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.db.database import get_menu_version, get_settings_version
from app.services.events import event_hub

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/{channel}")
async def websocket_endpoint(websocket: WebSocket, channel: str) -> None:
    """
    WebSocket connection grouped by channel.

    Channels:
        - "general"          — menu and settings change events
        - "kitchen"          — order lifecycle events
        - "orders_{order_id}" — individual order tracking
    """
    await event_hub.connect(websocket, channel)

    try:
        # Send a welcome message with current version hashes
        welcome = {
            "type": "welcome",
            "data": {
                "channel": channel,
                "menu_version": get_menu_version(),
                "settings_version": get_settings_version(),
            },
        }
        await websocket.send_text(json.dumps(welcome))

        # Keep the connection alive and listen for client messages
        while True:
            data = await websocket.receive_text()
            # Clients can send a ping; we reply with pong
            if data.strip().lower() == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        event_hub.disconnect(websocket, channel)
    except Exception:
        event_hub.disconnect(websocket, channel)
