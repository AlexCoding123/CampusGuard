import socket
import time
from concurrent.futures import ThreadPoolExecutor

import cv2 as cv
import numpy as np
import socketio
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from opencv_service import process_worker_single, clear_incident_dirs

load_dotenv()

# --- PER-SESSION STATE ---
# sid -> {"frames": [], "last_clip_time": float}
phone_sessions: dict = {}
clip_number = 0
executor = ThreadPoolExecutor(max_workers=5)

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
app = FastAPI()
socket_app = socketio.ASGIApp(sio, app)

clear_incident_dirs()

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:  # noqa: E722
        return "127.0.0.1"


LOCAL_IP = get_local_ip()

# ---------------------------------------------------------------------------
# Phone page — what the phone opens in its browser
# ---------------------------------------------------------------------------
PHONE_PAGE = """
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CampusGuard Camera</title>
  <style>
    body { margin:0; background:#111; display:flex; flex-direction:column;
           align-items:center; justify-content:center; height:100vh; font-family:sans-serif; }
    h2 { color:#fff; margin-bottom:8px; }
    video { width:100%; max-width:480px; border-radius:8px; }
    #status { margin-top:12px; font-size:1em; color:lime; text-align:center; padding:0 16px; }
  </style>
</head>
<body>
  <h2>CampusGuard Camera</h2>
  <video id="video" autoplay playsinline muted></video>
  <p id="status">Starting camera...</p>

  <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
  <script>
    const video  = document.getElementById('video');
    const status = document.getElementById('status');

    // Canvas is created once and never resized — resizing clears the canvas
    // and is expensive on mobile.
    const canvas = document.createElement('canvas');
    canvas.width  = 640;
    canvas.height = 480;
    const ctx = canvas.getContext('2d');

    const socket = io({
      transports: ['websocket'],
      reconnectionDelay: 1000,
      reconnectionAttempts: Infinity,
    });

    let stream     = null;
    let frameTimer = null;
    let sending    = false;   // back-pressure guard — skip frame if previous not sent yet

    function startCamera() {
      navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      }).then(s => {
        stream = s;
        video.srcObject = s;
        status.textContent = 'Camera ready.';
        if (socket.connected) startSending();
      }).catch(err => {
        status.textContent = 'Camera error: ' + err;
        status.style.color = 'red';
      });
    }

    function startSending() {
      if (frameTimer) return;
      status.textContent = 'Streaming…';
      status.style.color = 'lime';
      frameTimer = setInterval(() => {
        if (!socket.connected || sending || video.videoWidth === 0) return;
        sending = true;
        ctx.drawImage(video, 0, 0, 640, 480);
        canvas.toBlob(blob => {
          if (!blob) { sending = false; return; }
          blob.arrayBuffer()
            .then(buf => socket.emit('frame', buf))
            .catch(() => {})
            .finally(() => { sending = false; });
        }, 'image/jpeg', 0.5);  // quality 0.5 — good enough for AI analysis, half the bytes
      }, 150);  // ~6-7 FPS
    }

    function stopSending() {
      if (frameTimer) { clearInterval(frameTimer); frameTimer = null; }
      sending = false;
    }

    socket.on('connect', () => {
      status.textContent = stream ? 'Reconnected — streaming.' : 'Connected.';
      status.style.color = 'lime';
      if (stream) startSending();
    });

    socket.on('disconnect', () => {
      status.textContent = 'Disconnected — reconnecting…';
      status.style.color = 'orange';
      stopSending();
    });

    startCamera();
  </script>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# Viewer page — desktop browser watching the live phone feed
# ---------------------------------------------------------------------------
VIEW_PAGE = """
<!DOCTYPE html>
<html>
<head>
  <title>CampusGuard Live Feed</title>
  <style>
    * { box-sizing:border-box; margin:0; padding:0; }
    body { background:#000; display:flex; flex-direction:column;
           align-items:center; justify-content:center; height:100vh; font-family:monospace; }
    .cam-wrapper { position:relative; width:100%; max-width:900px; }
    img { width:100%; display:block; }
    .overlay-top {
      position:absolute; top:0; left:0; right:0; padding:8px 14px;
      background:linear-gradient(to bottom, rgba(0,0,0,0.75), transparent);
      display:flex; justify-content:space-between; align-items:center;
    }
    .cam-name     { color:#fff; font-size:0.95em; font-weight:bold; letter-spacing:1px; }
    .cam-location { color:#bbb; font-size:0.8em; }
    .overlay-bottom {
      position:absolute; bottom:0; left:0; right:0; padding:8px 14px;
      background:linear-gradient(to top, rgba(0,0,0,0.75), transparent);
      display:flex; justify-content:space-between; align-items:center;
    }
    .timestamp { color:#fff; font-size:0.9em; letter-spacing:1px; }
    .rec { display:flex; align-items:center; gap:6px; color:#ff3333; font-size:0.85em; font-weight:bold; }
    .rec-dot { width:10px; height:10px; border-radius:50%; background:#ff3333; animation:blink 1s infinite; }
    @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
    #conn-status { color:gray; font-size:0.8em; margin-top:8px; }
  </style>
</head>
<body>
  <div class="cam-wrapper">
    <img id="feed" />
    <div class="overlay-top">
      <div>
        <div class="cam-name">CAM 03 — HALLWAY B</div>
        <div class="cam-location">John Abbott College — Building H</div>
      </div>
      <div class="rec"><div class="rec-dot"></div>REC</div>
    </div>
    <div class="overlay-bottom">
      <div class="timestamp" id="timestamp">--:--:--</div>
    </div>
  </div>
  <p id="conn-status">Connecting…</p>

  <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
  <script>
    setInterval(() => {
      const now = new Date();
      document.getElementById('timestamp').textContent =
        now.toLocaleDateString('en-CA') + '  ' + now.toTimeString().split(' ')[0];
    }, 1000);

    const socket = io({ transports: ['websocket'] });
    const feed   = document.getElementById('feed');
    const conn   = document.getElementById('conn-status');

    socket.on('connect',    () => { conn.textContent = 'Connected. Waiting for phone…'; });
    socket.on('disconnect', () => { conn.textContent = 'Disconnected…'; });

    // Reuse a single object URL, revoking the previous one to avoid memory leaks
    let prevUrl = null;
    socket.on('live_frame', data => {
      const blob = new Blob([data], { type: 'image/jpeg' });
      const url  = URL.createObjectURL(blob);
      feed.src   = url;
      if (prevUrl) URL.revokeObjectURL(prevUrl);
      prevUrl = url;
      conn.textContent = '';
    });
  </script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Socket.IO events
# ---------------------------------------------------------------------------

@sio.on("connect")  # type: ignore
async def on_connect(sid, environ):
    phone_sessions[sid] = {"frames": [], "last_clip_time": time.time()}
    print(f"📱 Phone connected: {sid}")


@sio.on("disconnect")  # type: ignore
async def on_disconnect(sid):
    # Drop any buffered frames so they don't bleed into the next session
    phone_sessions.pop(sid, None)
    print(f"📱 Phone disconnected: {sid}")


@sio.on("frame")  # type: ignore
async def on_frame(sid, data):
    global clip_number

    session = phone_sessions.get(sid)
    if session is None:
        return

    # Forward raw JPEG to the viewer page immediately (live feed)
    await sio.emit("live_frame", data, skip_sid=sid)

    # Decode JPEG → OpenCV frame
    arr   = np.frombuffer(data, dtype=np.uint8)
    frame = cv.imdecode(arr, cv.IMREAD_COLOR)
    if frame is None:
        return

    session["frames"].append(frame)

    # Cut a clip every 15 frames (~2 s at 6-7 FPS)
    if len(session["frames"]) >= 15:
        clip_number += 1
        frames   = session["frames"].copy()
        elapsed  = time.time() - session["last_clip_time"]

        session["frames"].clear()
        session["last_clip_time"] = time.time()

        h, w = frames[0].shape[:2]
        print(f"✂️  Clip {clip_number} — {len(frames)} frames from {sid[:6]}")
        executor.submit(process_worker_single, frames, clip_number, elapsed, w, h)


# ---------------------------------------------------------------------------
# FastAPI routes
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index():
    return PHONE_PAGE


@app.get("/view", response_class=HTMLResponse)
async def view():
    return VIEW_PAGE



if __name__ == "__main__":
    print("\n🚀 CampusGuard — Phone Camera")
    print(f"📱 Phone  → http://{LOCAL_IP}:5050  (or ngrok HTTPS URL)")
    print(f"💻 Viewer → http://{LOCAL_IP}:5050/view\n")
    uvicorn.run(socket_app, host="0.0.0.0", port=5050)
