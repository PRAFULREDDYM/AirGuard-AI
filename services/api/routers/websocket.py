from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.ingestion.service import ws_manager

router = APIRouter(tags=["WebSocket"])

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        # Send initial connection acknowledgment
        await websocket.send_json({
            "type": "connection_established",
            "message": "Connected to AirGuard AI real-time event & telemetry stream."
        })
        while True:
            data = await websocket.receive_text()
            # Respond to client ping / heartbeat
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)

