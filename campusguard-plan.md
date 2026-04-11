# CampusGuard — AI Fight Detection for School CCTV

## JACHacks 2026 | 24h Hackathon | John Abbott College

### What We're Building
A real-time fight detection system that plugs into existing school CCTV cameras. When a fight is detected:
- Security staff get a **push notification** on their phone
- They open the **mobile app** and see: fight snapshot, camera location, confidence score
- Gemini API auto-generates a written incident report from the footage
- ElevenLabs generates a voice alert ("Altercation detected, Camera 3, Hallway B")
- Backend deployed on Vultr cloud, app served via campusguard.tech

### Sponsor Challenges We're Targeting
1. **Gemini API** — auto-generated incident reports from fight frames
2. **ElevenLabs** — real-time voice alerts for security
3. **Vultr** — backend deployed on Vultr cloud
4. **.Tech Domain** — campusguard.tech

---

## Stack

| Layer | Tech | Install |
|-------|------|---------|
| Video I/O | OpenCV | `pip install opencv-python` |
| Person detection | YOLOv8 | `pip install ultralytics` |
| Pose estimation | MediaPipe | `pip install mediapipe` |
| Fight logic | Custom Python | — |
| Backend | Flask + SocketIO | `pip install flask flask-socketio` |
| Mobile App | React Native (Expo) | `npx create-expo-app campusguard-app` |
| Push Notifications | Expo Notifications | Built into Expo |
| Incident reports | Gemini API | `pip install google-generativeai` |
| Voice alerts | ElevenLabs API | `pip install elevenlabs` |
| Hosting | Vultr VM | Ubuntu, set up on day |
| Domain | .tech | Use code JAC26 |

---

## How It Works

```
Camera / Video file
  -> OpenCV reads frames
  -> YOLOv8 detects all people (bounding boxes)
  -> MediaPipe extracts skeleton pose per person
  -> Fight detection logic checks pairs:
       - Are two people close together?
       - Are arms moving fast? (punching)
       - Are arms extended toward each other?
       - Has this been going on for 1-2 seconds?
  -> If fight score > threshold:
       -> Send frame to Gemini API -> get incident report
       -> Send alert text to ElevenLabs -> get voice audio
       -> Save snapshot + report to backend
       -> Send push notification to mobile app
       -> User opens app -> sees snapshot, report, plays voice alert
```

---

## Team Roles

### P1 — CV Pipeline (the engine)

**You own:** YOLOv8 + MediaPipe + fight detection logic

| Time | Task |
|------|------|
| 0-1h | Set up Python env, install opencv, ultralytics, mediapipe |
| 1-4h | Core pipeline: video input -> YOLOv8 person detection -> MediaPipe pose per person |
| 4-7h | Fight detection heuristics: proximity, arm velocity, aggression scoring |
| 7-10h | Simple centroid tracking (consistent person IDs across frames) |
| 10-14h | Tune thresholds on demo videos |
| 14-18h | Optimize, handle edge cases |
| 18-24h | Integration help, bug fixes, demo rehearsal |

**Your deliverable:** A Python function that takes a frame and returns: list of people with skeletons + fight alerts with confidence scores

**Key export for P2:**
```python
def process_frame(frame):
    # returns:
    # {
    #   "people": [{"id": 1, "bbox": [...], "keypoints": [...]}],
    #   "alerts": [{"pair": [1, 2], "score": 0.87, "type": "fight"}],
    #   "annotated_frame": frame_with_drawings
    # }
```

---

### P2 — Backend + API Integrations

**You own:** Flask server, Gemini API, ElevenLabs API

| Time | Task |
|------|------|
| 0-1h | Set up Flask project, get API keys (Gemini + ElevenLabs) |
| 1-3h | Flask server with REST API: POST /alerts, GET /alerts, GET /alerts/:id |
| 3-6h | **Start with fake/hardcoded alerts** — don't wait for P1 |
| 6-9h | Gemini integration: send fight frame -> get incident report text |
| 9-12h | ElevenLabs integration: send alert text -> get audio file -> store + serve |
| 12-14h | Expo push notification integration: send push when fight detected |
| 14-18h | Wire in P1's real pipeline (swap fake data for real), alert history (SQLite) |
| 18-24h | Polish, help P4 deploy to Vultr |

**Your deliverable:** Flask API that receives fight detections, generates reports/audio, stores alerts, sends push notifications to mobile app

**API keys needed:**
- Gemini: https://makersuite.google.com/app/apikey
- ElevenLabs: Check email with subject "Everything You Need to Know about MLH at JACHacks"

---

### P3 — Mobile App (React Native / Expo)

**You own:** The mobile app that security staff use

| Time | Task |
|------|------|
| 0-1h | `npx create-expo-app campusguard-app`, set up Expo project |
| 1-3h | Set up Expo push notifications (expo-notifications) |
| 3-6h | **Alert list screen**: scrollable list of fight alerts (timestamp, camera, confidence badge) |
| 6-9h | **Alert detail screen**: tap alert -> see fight snapshot image, Gemini incident report, camera info |
| 9-12h | ElevenLabs audio playback: play button on detail screen to hear voice alert |
| 12-15h | Connect to P2's backend API (fetch alerts, register push token) |
| 15-18h | Push notification handling: tap notification -> opens alert detail screen |
| 18-20h | Visual polish: red urgency styling, smooth animations, app icon |
| 20-24h | Final polish, demo rehearsal |

**Your deliverable:** Mobile app that receives push notifications on fight detection, shows snapshot + report + audio

**Start with mock data!** Don't wait for P2. Hardcode fake alerts like:
```json
{
  "id": "alert_001",
  "timestamp": "2026-04-12 14:32:05",
  "camera": "Camera 3 - Hallway B",
  "confidence": 0.87,
  "snapshot_url": "https://via.placeholder.com/640x480",
  "report": "Two individuals engaged in physical altercation near lockers...",
  "audio_url": "https://example.com/sample-alert.mp3"
}
```
Swap for real API calls when P2 is ready.

**App screens:**
1. **Alert List** — all recent alerts, newest first, red badge for unreviewed
2. **Alert Detail** — fight snapshot, Gemini report, play ElevenLabs audio, camera/time info
3. **Settings** (stretch goal) — select which cameras to monitor, notification preferences

---

### P4 — DevOps, Demo & Presentation

**You own:** Vultr, domain, demo videos, presentation

| Time | Task |
|------|------|
| 0-1h | Register campusguard.tech (code: JAC26), spin up Vultr VM (code: MAJORLEAGUEHACKING) |
| 1-3h | Find 5-10 demo videos: CCTV fight clips + normal hallway footage |
| 3-5h | Set up phone as IP webcam (DroidCam) for live demo option |
| 5-8h | Help P1 test pipeline with demo videos |
| 8-12h | Deploy backend to Vultr (Python + nginx + SSL) |
| 12-16h | Build presentation deck |
| 16-20h | Full end-to-end test on Vultr |
| 20-24h | Rehearse demo, record backup screen recording |

**Your deliverable:** Working deployment + polished presentation + reliable demo

**Demo video sources:** Search YouTube for "CCTV fight" or "school fight caught on camera". Download with yt-dlp.

---

## Handoff Points

| When | What | From -> To |
|------|------|------------|
| Hour 3 | P1 has basic frame processing | P1 -> P2 connects backend |
| Hour 3 | P2 has REST API running | P2 -> P3 connects mobile app |
| Hour 6 | P1 has fight detection returning alerts | P1 -> P2 uses real alerts |
| Hour 12 | P2 has Gemini + ElevenLabs + push working | P2 -> P3 uses real data |
| Hour 14 | P2 has backend ready to deploy | P2 -> P4 deploys to Vultr |

**KEY RULE: P2, P3, P4 — DO NOT WAIT for dependencies. Build with fake/mock data first, swap in real data later. Integration should take 15 min, not a rebuild.**

---

## Parallel Work Diagram

```
Hour 0                                                    Hour 24
|                                                              |
P1: [==== CV pipeline (independent) ====][== tuning ==][bugfix]
                                         |
P2: [== Flask + APIs w/ fake data ==][== wire to P1 ==][polish]
                                      |
P3: [== Mobile app w/ mock data ==][== wire to P2 ==][polish]
                                                              
P4: [== Vultr + domain + videos + presentation (independent) =]
```

---

## Presentation Pitch Structure

1. **The Problem** (30 sec): Schools have CCTV everywhere but nobody watching 24/7. Fights go unnoticed. Staff respond late.
2. **The Solution** (30 sec): CampusGuard — AI that watches the cameras and alerts security instantly.
3. **Live Demo** (2 min): Show fight video -> system detects it -> phone gets push notification -> open app -> snapshot + report + voice alert
4. **How It Works** (1 min): YOLO finds people, MediaPipe reads body language, custom logic scores aggression
5. **Sponsor Integrations** (1 min): Gemini writes reports, ElevenLabs voices alerts, hosted on Vultr at campusguard.tech
6. **Why Schools Would Install This** (30 sec): Uses existing cameras, no new hardware, instant alerts, automatic documentation
