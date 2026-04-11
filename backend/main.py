import asyncio
import os
import uuid
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from gemini_service import analyze_clip
from pydantic import BaseModel

from camera_service import start_recording

load_dotenv()

app = FastAPI(title="CampusGuard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory alert storage
alerts_db: list[dict] = []

# Store expo push tokens
push_tokens: list[str] = []

# Recording state
is_recording = False


class DeviceToken(BaseModel):
    token: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/start")
async def start():
    """Start the camera recording + Gemini analysis loop."""
    global is_recording
    if is_recording:
        return {"status": "already running"}
    is_recording = True
    asyncio.create_task(recording_loop())
    return {"status": "started"}


@app.post("/stop")
async def stop():
    """Stop the camera recording loop."""
    global is_recording
    is_recording = False
    return {"status": "stopped"}


async def recording_loop():
    """Records 10-second clips and sends each to Gemini for analysis."""
    global is_recording
    clip_number = 0

    while is_recording:
        clip_number += 1
        os.makedirs("static/clips", exist_ok=True)
        clip_path = f"static/clips/clip_{clip_number}.mp4"

        # Record a 10-second clip
        await asyncio.to_thread(start_recording, clip_path, duration=10)

        # Send to Gemini async (don't block the next recording)
        asyncio.create_task(process_clip(clip_path, clip_number))


async def process_clip(clip_path: str, clip_number: int):
    """Send clip to Gemini, create alert if fight detected."""
    result = await asyncio.to_thread(analyze_clip, clip_path)

    if result["is_fight"]:
        alert_id = str(uuid.uuid4())
        alert = {
            "id": alert_id,
            "timestamp": datetime.now().isoformat(),
            "camera": "Camera 1",
            "confidence": result["confidence"],
            "clip_url": f"/{clip_path}",
            "report": result["report"],
            "audio_url": None,  # TODO: ElevenLabs integration
        }
        alerts_db.insert(0, alert)

        # TODO: Send push notification to registered devices


@app.get("/alerts")
def get_alerts():
    """Mobile app fetches all alerts, newest first."""
    return alerts_db


@app.get("/alerts/{alert_id}")
def get_alert(alert_id: str):
    """Mobile app fetches a single alert by ID."""
    for alert in alerts_db:
        if alert["id"] == alert_id:
            return alert
    return {"error": "Alert not found"}


@app.post("/register-device")
def register_device(device: DeviceToken):
    """Mobile app registers its Expo push token for notifications."""
    if device.token not in push_tokens:
        push_tokens.append(device.token)
    return {"status": "registered"}


# Serve static files (clips, snapshots)
os.makedirs("static/clips", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
