import os
import uuid
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from api.notification import notification_router

load_dotenv()

app = FastAPI(title="CampusGuard API")

app.include_router(notification_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory alert storage (good enough for hackathon)
alerts_db: list[dict] = []

# Store expo push tokens
push_tokens: list[str] = []


# --- Models ---


class DeviceToken(BaseModel):
    token: str


# --- Routes ---


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/alerts")
async def create_alert(
    snapshot: UploadFile = File(...),
    camera: str = "Unknown Camera",
    confidence: float = 0.0,
):
    """P1's CV pipeline calls this when a fight is detected.
    Sends snapshot image, camera ID, and confidence score."""
    alert_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()

    # Save snapshot image
    # os.makedirs("static/snapshots", exist_ok=True)
    # snapshot_path = f"static/snapshots/{alert_id}.jpg"
    # with open(snapshot_path, "wb") as f:
    #     f.write(await snapshot.read())

    # TODO: Gemini integration — generate incident report from snapshot
    report = "Incident report pending..."

    # TODO: ElevenLabs integration — generate voice alert audio
    audio_url = None

    # TODO: Send push notification to registered devices

    alert = {
        "id": alert_id,
        "timestamp": timestamp,
        "camera": camera,
        "confidence": confidence,
        "snapshot_url": f"/{snapshot_path}",
        "report": report,
        "audio_url": audio_url,
    }
    alerts_db.insert(0, alert)

    return alert


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


# Serve snapshot images
# os.makedirs("static/snapshots", exist_ok=True)
# app.mount("/static", StaticFiles(directory="static"), name="static")
os.makedirs("incidents", exist_ok=True)
app.mount("/incidents", StaticFiles(directory="incidents"), name="incidents")
