import os
import queue
import socket
import threading
import time

import cv2 as cv
import numpy as np
import socketio
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse

import asyncio, json, queue as q
from shared import alert_queue

from camera_service import process_worker

load_dotenv()

# --- CLIP RECORDING FROM PHONE FRAMES ---
frame_buffer = []
clip_number = 0
last_clip_time = time.time()

# Start the AI worker thread (same as camera_service)
os.makedirs("videos", exist_ok=True)
job_queue = queue.Queue()
ai_thread = threading.Thread(target=process_worker, args=(job_queue,), daemon=True)
ai_thread.start()

# 1. Setup Socket.IO AsyncServer
# We use 'asyncio' mode for FastAPI compatibility
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
app = FastAPI()
# Combine FastAPI and Socket.IO into one application
socket_app = socketio.ASGIApp(sio, app)


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

# --- HTML TEMPLATES (Kept exactly as your original) ---
PHONE_PAGE = """
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CampusGuard Camera</title>
  <style>
    body { margin:0; background:#111; display:flex; flex-direction:column;
           align-items:center; justify-content:center; height:100vh; font-family:sans-serif; }
    h2 { color:#fff; }
    video { width:100%; max-width:480px; border-radius:8px; }
    #status { color:lime; margin-top:12px; font-size:1em; }
  </style>
</head>
<body>
  <h2>CampusGuard Camera</h2>
  <video id="video" autoplay playsinline muted></video>
  <p id="status">Waiting...</p>
  <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
  <script>
    const socket = io({ transports: ['websocket'] });
    const status = document.getElementById('status');
    const video  = document.getElementById('video');
    const pc = new RTCPeerConnection({ iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] });

    navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment', width: 1280, height: 720 }, audio: false
    }).then(stream => {
      video.srcObject = stream;
      stream.getTracks().forEach(track => pc.addTrack(track, stream));
      status.textContent = 'Camera ready. Waiting for viewer...';
    }).catch(err => { status.textContent = 'Camera error: ' + err; status.style.color='red'; });

    socket.on('viewer_ready', async () => {
      status.textContent = 'Viewer connected!';
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);
      socket.emit('offer', offer);
    });

    socket.on('answer', async (answer) => {
      await pc.setRemoteDescription(new RTCSessionDescription(answer));
      status.textContent = 'Streaming live!';
    });

    socket.on('ice_candidate', async ({ candidate }) => {
      try { await pc.addIceCandidate(new RTCIceCandidate(candidate)); } catch(e) {}
    });

    pc.onicecandidate = ({ candidate }) => {
      if (candidate) socket.emit('phone_ice', { candidate });
    };

    // Send frames to server
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    setInterval(() => {
      if (video.videoWidth === 0) return;
      canvas.width = 1280;
      canvas.height = 720;
      ctx.drawImage(video, 0, 0, 1280, 720);
      canvas.toBlob(blob => {
        blob.arrayBuffer().then(buf => socket.emit('frame', buf));
      }, 'image/jpeg', 0.85);
    }, 200);
  </script>
</body>
</html>
"""


VIEW_PAGE = """
<!DOCTYPE html>
<html>
<head>
  <title>CampusGuard Live Feed</title>
  <style>
    * { box-sizing: border-box; margin:0; padding:0; }
    body { background:#000; display:flex; flex-direction:column;
           align-items:center; justify-content:center; height:100vh; font-family:monospace; }

    .cam-wrapper { position:relative; width:100%; max-width:900px; }

    video { width:100%; display:block; }

    /* Top bar */
    .overlay-top {
      position:absolute; top:0; left:0; right:0;
      padding:8px 14px;
      background:linear-gradient(to bottom, rgba(0,0,0,0.75), transparent);
      display:flex; justify-content:space-between; align-items:center;
    }
    .cam-name { color:#fff; font-size:0.95em; font-weight:bold; letter-spacing:1px; }
    .cam-location { color:#bbb; font-size:0.8em; }

    /* Bottom bar */
    .overlay-bottom {
      position:absolute; bottom:0; left:0; right:0;
      padding:8px 14px;
      background:linear-gradient(to top, rgba(0,0,0,0.75), transparent);
      display:flex; justify-content:space-between; align-items:center;
    }
    .timestamp { color:#fff; font-size:0.9em; letter-spacing:1px; }
    .persons   { color:#00ff00; font-size:0.85em; }

    /* REC dot */
    .rec { display:flex; align-items:center; gap:6px; color:#ff3333; font-size:0.85em; font-weight:bold; }
    .rec-dot { width:10px; height:10px; border-radius:50%; background:#ff3333;
               animation: blink 1s infinite; }
    @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }

    #conn-status { color:gray; font-size:0.8em; margin-top:8px; }
  </style>
</head>
<body>
  <div class="cam-wrapper">
    <img id="feed" style="width:100%; display:block;" />

    <div class="overlay-top">
      <div>
        <div class="cam-name">CAM 03 — HALLWAY B</div>
        <div class="cam-location">John Abbott College — Building H</div>
      </div>
      <div class="rec"><div class="rec-dot"></div>REC</div>
    </div>

    <div class="overlay-bottom">
      <div class="timestamp" id="timestamp">--:--:--</div>
      <div class="persons" id="persons">LIVE</div>
    </div>
  </div>
  <p id="conn-status">Connecting...</p>

  <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
  <script>
    // Live timestamp
    function updateTime() {
      const now = new Date();
      const date = now.toLocaleDateString('en-CA');
      const time = now.toTimeString().split(' ')[0];
      document.getElementById('timestamp').textContent = date + '  ' + time;
    }
    setInterval(updateTime, 1000);
    updateTime();

    const socket = io({ transports: ['websocket'] });
    const feed = document.getElementById('feed');
    const conn = document.getElementById('conn-status');

    socket.on('connect', () => {
      conn.textContent = 'Connected. Waiting for phone...';
    });

    socket.on('live_frame', (data) => {
      const blob = new Blob([data], { type: 'image/jpeg' });
      feed.src = URL.createObjectURL(blob);
      conn.textContent = '';
    });
  </script>
</body>
</html>
"""

# --- SOCKET.IO EVENTS (Using async syntax) ---


@sio.on("connect")  # type: ignore
async def on_connect(sid, environ):
    print(f"[SOCKET] Client connected: {sid}")


@sio.on("disconnect")  # type: ignore
async def on_disconnect(sid):
    print(f"[SOCKET] Client disconnected: {sid}")


@sio.on("viewer_ready")  # type: ignore
async def on_viewer_ready(sid):
    print(f"[SIGNAL] Viewer ready (from {sid})")
    await sio.emit("viewer_ready", skip_sid=sid)


@sio.on("offer")  # type: ignore
async def on_offer(sid, data):
    print(f"[SIGNAL] Offer received (from {sid})")
    await sio.emit("offer", data, skip_sid=sid)


@sio.on("answer")  # type: ignore
async def on_answer(sid, data):
    print(f"[SIGNAL] Answer received (from {sid})")
    await sio.emit("answer", data, skip_sid=sid)


@sio.on("phone_ice")  # type: ignore
async def on_phone_ice(sid, data):
    print(f"[ICE] Phone ICE candidate (from {sid})")
    await sio.emit("ice_candidate", data, skip_sid=sid)


@sio.on("viewer_ice")  # type: ignore
async def on_viewer_ice(sid, data):
    print(f"[ICE] Viewer ICE candidate (from {sid})")
    await sio.emit("ice_candidate", data, skip_sid=sid)


# --- FRAME CAPTURE FOR GEMINI ANALYSIS ---


@sio.on("frame")  # type: ignore
async def on_frame(sid, data):
    global frame_buffer, clip_number, last_clip_time

    # Decode JPEG bytes into an OpenCV frame
    arr = np.frombuffer(data, dtype=np.uint8)
    frame = cv.imdecode(arr, cv.IMREAD_COLOR)
    if frame is None:
        return

    frame_buffer.append(frame)
    if len(frame_buffer) % 10 == 1:
        print(f"[FRAME] Receiving frames... ({len(frame_buffer)} buffered)")

    # Only cut a clip when we have at least 15 frames
    if len(frame_buffer) >= 15:
        clip_number += 1
        frames = frame_buffer.copy()
        frame_buffer.clear()
        elapsed = time.time() - last_clip_time
        last_clip_time = time.time()

        h, w = frames[0].shape[:2]
        print(f"[CLIP] Buffered {len(frames)} frames, sending to worker...")
        job_queue.put((frames, clip_number, elapsed, w, h))


# --- FASTAPI ROUTES ---


@app.get("/", response_class=HTMLResponse)
async def index():
    return PHONE_PAGE


@app.get("/view", response_class=HTMLResponse)
async def view():
    return VIEW_PAGE

@app.get("/events")
async def sse_events():
    async def stream():
        while True:
            try:
                event = alert_queue.get_nowait()
                yield f"data: {json.dumps(event)}\n\n"
            except q.Empty:
                await asyncio.sleep(0.5)
    return StreamingResponse(stream(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn

    print("\n🚀 CampusGuard — Live Camera (FastAPI)")
    print(f"📡 Local IP: http://{LOCAL_IP}:5000")
    print("📱 Phone  → open ngrok HTTPS URL in phone browser")
    print("💻 Viewer → http://localhost:5000/view\n")

    # We run 'socket_app' (the wrapped app) instead of 'app'
    uvicorn.run(socket_app, host="0.0.0.0", port=5050)
