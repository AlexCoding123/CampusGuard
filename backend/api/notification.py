from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse
import asyncio
import json
from datetime import datetime

notification_router = APIRouter(prefix="/alerts", tags=["alerts"])

# Holds all connected Flutter clients
alert_queues: list[asyncio.Queue] = []


@notification_router.get("/stream")
async def stream_alerts(request: Request):
    queue = asyncio.Queue()
    alert_queues.append(queue)
    print(f"Client connected. Total clients: {len(alert_queues)}")

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    print("Client disconnected.")
                    break
                try:
                    alert = await asyncio.wait_for(queue.get(), timeout=30)
                    yield {
                        "event": "threat",
                        "data": json.dumps(alert)
                    }
                except asyncio.TimeoutError:
                    # Keep connection alive
                    yield {"event": "heartbeat", "data": "ping"}
        finally:
            alert_queues.remove(queue)
            print(f"Client removed. Total clients: {len(alert_queues)}")

    return EventSourceResponse(event_generator())


@notification_router.post("/send")
async def send_alert(alert: dict):
    payload = {
        "id": str(datetime.now().timestamp()),
        "timestamp": datetime.now().isoformat(),
        "location": alert.get("location", "Unknown"),
        "threat_level": alert.get("threat_level", "HIGH"),
        "description": alert.get("description", ""),
        "video_url": alert.get("video_url", ""),
        "lat": str(alert.get("lat", "")),
        "lng": str(alert.get("lng", ""))
    }

    if not alert_queues:
        return {"status": "no clients connected", "sent_to": 0}

    for queue in alert_queues:
        await queue.put(payload)

    print(f"Alert sent to {len(alert_queues)} client(s)")
    return {"status": "sent", "sent_to": len(alert_queues), "payload": payload}


@notification_router.get("/test")
async def test_alert():
    """Hit this from your browser to send a fake alert — useful for testing"""
    payload = {
        "id": str(datetime.now().timestamp()),
        "timestamp": datetime.now().isoformat(),
        "location": "Main entrance - Camera 1",
        "threat_level": "MEDIUM",
        "description": "Unidentified person with suspicious behavior detected by Gemini",
        "video_url": "",
        "lat": "45.5017",
        "lng": "-73.5673"
    }

    if not alert_queues:
        return {"status": "no clients connected"}

    for queue in alert_queues:
        await queue.put(payload)

    return {"status": "test alert sent", "sent_to": len(alert_queues)}