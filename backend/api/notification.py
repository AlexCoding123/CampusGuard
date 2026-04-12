import os
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse
import asyncio
import json
from datetime import datetime, timezone

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
                    yield {"event": "threat", "data": json.dumps(alert)}
                except asyncio.TimeoutError:
                    yield {"event": "heartbeat", "data": "ping"}
        finally:
            alert_queues.remove(queue)
            print(f"Client removed. Total clients: {len(alert_queues)}")

    return EventSourceResponse(event_generator())


@notification_router.post("/send")
async def send_alert(alert: dict):
    payload = {
        "group_id": alert.get("group_id", "1"),
        "severity": alert.get("severity", "aggressive"),
        "confidence": round(float(alert.get("confidence", 0.5)), 2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "location": alert.get("location", "Camera 1 - Main Entrance"),
        "video_url": alert.get("video_url", ""),
        "report": alert.get("report", ""),
    }
    if not alert_queues:
        return {"status": "no clients connected", "sent_to": 0}
    for queue in alert_queues:
        await queue.put(payload)
    print(f"Alert sent to {len(alert_queues)} client(s)")
    return {"status": "sent", "sent_to": len(alert_queues), "payload": payload}


@notification_router.get("/test")
async def test_alert():
    if not alert_queues:
        return {"status": "no clients connected"}

    events = [
        # Group 1 — two videos together
        {
            "group_id": "1",
            "severity": "violent",
            "confidence": 0.87,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "location": "Camera 1 - Main Entrance",
            "video_url": "http://127.0.0.1:8000/alerts/media/shoot.mp4",
        },
        {
            "group_id": "1",
            "severity": "violent",
            "confidence": 0.91,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "location": "Camera 1 - Main Entrance",
            "video_url": "http://127.0.0.1:8000/alerts/media/shoot.mp4",
        },
        # Group 2 — solo
        {
            "group_id": "2",
            "severity": "critical",
            "confidence": 0.76,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "location": "Camera 2 - Parking Lot",
            "video_url": "http://127.0.0.1:8000/alerts/media/shoot.mp4",
        },
        # Group 3 — solo
        {
            "group_id": "3",
            "severity": "aggressive",
            "confidence": 0.63,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "location": "Camera 3 - Side Exit",
            "video_url": "http://127.0.0.1:8000/alerts/media/shoot.mp4",
        },
    ]

    for payload in events:
        for queue in alert_queues:
            await queue.put(payload)

    return {"status": "test alerts sent", "sent_to": len(alert_queues), "groups": 3, "total_events": 4}