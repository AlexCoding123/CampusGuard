import os
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse
import asyncio
import json
from datetime import datetime

notification_router = APIRouter(prefix="/alerts", tags=["alerts"])

alert_queues: list[asyncio.Queue] = []

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


@notification_router.get("/media/{filename}")
async def serve_media(filename: str):
    file_path = os.path.join(BASE_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="video/mp4")


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
        "video_url": "http://127.0.0.1:8000/alerts/media/shoot.mp4",
        "lat": "45.5017",
        "lng": "-73.5673"
    }
    if not alert_queues:
        return {"status": "no clients connected"}
    for queue in alert_queues:
        await queue.put(payload)
    return {"status": "test alert sent", "sent_to": len(alert_queues)}