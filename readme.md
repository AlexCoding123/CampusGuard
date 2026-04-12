# CampusGuard — AI Fight Detection System

CampusGuard is a real-time school security system that analyzes live camera feeds using Google Gemini 2.0 Flash to detect and classify violent incidents. When a fight is detected, it saves a video clip and immediately pushes an alert to a live web dashboard and a mobile app. It also detects critical moments when student life could be a danger such as a seizure.

---

## Architecture Overview

```
Phone/Webcam → camera_opener.py (port 5050)
                     │
                     ▼
           camera_service.py
           (frame buffering + Gemini analysis)
                     │
                     ▼
              main.py API (port 8080)
           ┌─────────┴──────────┐
           ▼                    ▼
   notification_web         Flutter app
   React dashboard          (iOS / Android)
   (port 3000)
```

**Three independent services** need to run simultaneously:
1. **Backend** — FastAPI server that stores and streams alerts
2. **Camera service** — captures frames, runs AI analysis, sends alerts
3. **Web dashboard** — React frontend that displays alerts in real time

---

## Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.12+ | |
| Node.js | 18+ | For the web dashboard |
| npm | 9+ | Comes with Node.js |
| uv | latest | Python package manager — [install](https://docs.astral.sh/uv/getting-started/installation/) |
| Google Gemini API key | — | [Get one here](https://aistudio.google.com/app/apikey) |

> **No system FFmpeg required.** The Python package `imageio[ffmpeg]` bundles its own.

---

## Setup

### 1. Clone the repository

```bash
git clone <repo-url>
cd JackHacks2026
```

### 2. Configure environment variables

Create a `.env` file inside the `backend/` folder:

```bash
cd backend
cp .env.example .env   # if it exists, otherwise create it manually
```

Add the following to `backend/.env`:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Install Python dependencies

From the `backend/` folder:

```bash
cd backend
uv sync
```

This installs all dependencies listed in `pyproject.toml` into a local virtual environment (`.venv`).

### 4. Install web dashboard dependencies

```bash
cd notification_web
npm install
```

---

## Running the Project

Open **three separate terminals** and run each command from the project root.

### Terminal 1 — Backend API (port 8080)

```bash
cd backend
uv run uvicorn main:app --host 0.0.0.0 --port 8080
```

Serves the alert API and streams events to the dashboard via SSE.

### Terminal 2 — Camera Service

**Option A: Use your webcam**

```bash
cd backend
uv run python camera_service.py
```

A window titled "CCTV Feed" will open. Press `q` to stop.

**Option B: Use your phone as a camera**

```bash
cd backend
uv run python camera_opener.py
```

The terminal will print two URLs:

```
📱 Phone  → http://192.168.x.x:5050
💻 Viewer → http://192.168.x.x:5050/view
```

- Open the **Phone URL** on your phone's browser (must be on the same Wi-Fi network). Tap "Allow" when prompted for camera access.
- Open the **Viewer URL** on your desktop to watch the live feed.

### Terminal 3 — Web Dashboard (port 3000)

```bash
cd notification_web
npm start
```

Opens [http://localhost:3000](http://localhost:3000) automatically. The dashboard connects to the backend and displays alerts in real time.

---

## How It Works

1. **Frame capture** — The camera service captures frames continuously in 5-second clips.
2. **AI analysis** — Each clip's frames are sent as JPEG images to Gemini 2.0 Flash, which classifies the threat level:
   - `safe` — No action taken.
   - `aggressive` — Physical confrontation detected (yellow alert).
   - `critical` — Severe threat (weapon, person down, multiple attackers) (red alert).
3. **Incident grouping** — All clips of the same fight are grouped under one incident ID. The group closes when a `safe` clip is detected.
4. **Cooldown** — Once an alert fires, the same severity is suppressed for 30 seconds. Escalations (aggressive → critical) always fire immediately.
5. **Video clip** — Only violent clips are encoded to H.264 and saved in `backend/incidents/`.
6. **Alert push** — The backend queues the alert and pushes it to all connected clients via Server-Sent Events (SSE).
7. **Dashboard** — The React dashboard displays alert cards with severity, location, report, confidence, and a playable video clip.

---

## Project Structure

```
JackHacks2026/
├── backend/
│   ├── main.py                # FastAPI app — alert API, static file serving
│   ├── camera_service.py      # Webcam capture, clip processing, Gemini calls
│   ├── camera_opener.py       # Phone camera SocketIO server (port 5050)
│   ├── gemini.py              # Gemini 2.0 Flash integration
│   ├── api/
│   │   └── notification.py    # SSE stream, /alerts/send, /alerts/reset
│   ├── incidents/             # Saved H.264 clips (created at runtime)
│   ├── pyproject.toml         # Python dependencies
│   └── .env                   # API keys (not committed)
│
├── notification_web/
│   ├── src/
│   │   ├── App.js             # Main React component, SSE connection
│   │   ├── constants.js       # API base URL, severity colors
│   │   └── components/        # AlertCard, Modal, Header, StatusBar, etc.
│   └── package.json
│
├── notification/              # Flutter mobile app (iOS / Android)
│   └── lib/
│       ├── main.dart
│       ├── screens/           # Home screen with live alert list
│       ├── services/          # SSE client
│       └── widgets/           # Alert cards, detail sheet
│
└── README.md
```

---

## Testing Without a Camera

The backend exposes a test endpoint that injects a fake alert:

```bash
curl -X POST http://127.0.0.1:8080/test
```

This sends a mock `critical` alert to the dashboard so you can verify the frontend is working without needing a live camera feed.

---

## Troubleshooting

**Dashboard shows no alerts / "Disconnected"**
- Make sure the backend (Terminal 1) is running on port 8080 before starting the dashboard.

**Phone camera page says "Camera error"**
- The phone must be on the **same Wi-Fi network** as your computer.
- The URL must be accessed over HTTP (not HTTPS) — browsers allow camera access on local network HTTP.
- On iOS Safari, ensure camera permissions are granted in Settings.

**`GEMINI_API_KEY` not found error**
- Make sure `backend/.env` exists and contains `GEMINI_API_KEY=...`.
- Do not put the `.env` file in the project root — it must be inside `backend/`.

**Video clips not playing in Firefox / Vivaldi**
- The system uses H.264 (libx264) which requires the `imageio[ffmpeg]` package. Run `uv sync` again to make sure it is installed.

**Old alerts still showing after a fresh run**
- The backend calls `/alerts/reset` on startup, which clears the dashboard automatically. If the dashboard was open before the backend restarted, refresh the page.
