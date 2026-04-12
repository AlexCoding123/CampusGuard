import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

import cv2 as cv
import httpx
import imageio

from gemini import analyze_frames

# --- CONFIGURATION ---
CLIP_DURATION = 3

# --- INCIDENT GROUP TRACKING ---
_group_id = 0
_incident_active = False
_last_clip_time = 0.0
_last_severity_sent = None  # tracks highest severity fired so far
_group_lock = threading.Lock()

SEVERITY_RANK = {"aggressive": 1, "critical": 2}
COOLDOWN = 30  # seconds before the same severity can fire again


def _resolve_group(severity: str) -> str | None:
    """Decide whether to save and send a clip.

    Rules:
    - Safe clip          → close incident, return None
    - Escalation         → always send (aggressive → critical is new information)
    - Same severity      → send only if COOLDOWN seconds have passed
    """
    global _group_id, _incident_active, _last_clip_time, _last_severity_sent
    with _group_lock:
        if severity == "safe":
            _incident_active = False
            _last_severity_sent = None
            return None

        now = time.time()
        if not _incident_active:
            # New incident
            _group_id += 1
            _incident_active = True
            _last_clip_time = now
            _last_severity_sent = severity
            return str(_group_id)

        is_escalation = SEVERITY_RANK.get(severity, 0) > SEVERITY_RANK.get(
            _last_severity_sent or "", 0
        )
        cooldown_passed = now - _last_clip_time >= COOLDOWN

        if is_escalation or cooldown_passed:
            _last_clip_time = now
            _last_severity_sent = severity
            return str(_group_id)

        return None  # same severity, still within cooldown — block it


class CameraStream:
    """A dedicated class to fetch frames in a separate thread."""

    def __init__(self, source=0):
        self.cap = cv.VideoCapture(source)
        self.ret, self.frame = self.cap.read()
        self.stopped = False

    def start(self):
        threading.Thread(target=self.update, args=(), daemon=True).start()
        return self

    def update(self):
        while not self.stopped:
            if not self.ret:
                self.stop()
            else:
                self.ret, self.frame = self.cap.read()

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True
        self.cap.release()


def process_worker_single(frames, clip_number, duration):
    """Process a single clip in its own thread.

    Fast path: send raw frames as JPEG images to Gemini (no video encoding).
    Only encode H.264 when the clip is actually violent — safe clips are
    discarded immediately, saving both time and disk I/O.
    """
    actual_fps = len(frames) / duration
    print(
        f"🔍 Analyzing clip_{clip_number} ({len(frames)} frames @ {actual_fps:.1f} FPS)..."
    )
    try:
        result = analyze_frames(frames)

        severity = result.get("severity")
        report = result.get("report")

        group_id = _resolve_group(severity or "safe")

        if group_id is not None:
            # Only encode H.264 for violent clips
            os.makedirs("incidents", exist_ok=True)
            incident_path = f"incidents/clip_{clip_number}.mp4"
            safe_fps = min(60.0, max(1.0, float(actual_fps)))
            with imageio.get_writer(
                incident_path,
                fps=safe_fps,
                codec="libx264",
                output_params=["-pix_fmt", "yuv420p", "-crf", "23", "-preset", "fast"],
            ) as vid_writer:
                for frame in frames:
                    small = cv.resize(frame, (720, 544))
                    vid_writer.append_data(small[:, :, ::-1])  # BGR → RGB

            print(f"🚨 {incident_path}: VIOLENT (group {group_id}) — {report}\n")
            httpx.post(
                "https://sse.campusguard.tech/alerts/send",
                json={
                    "group_id": group_id,
                    "severity": severity,
                    "confidence": round(float(result.get("confidence", 0.5)), 2),
                    "timestamp": datetime.now(UTC).isoformat(),
                    "location": "Camera 1 - Main Entrance",
                    "video_url": f"https://sse.campusguard.tech/incidents/clip_{clip_number}.mp4",
                    "report": report or "",
                },
            )
        else:
            print(f"✅ Clear: clip_{clip_number} — incident closed\n")
    except Exception as e:
        print(f"❌ Error: {e}")


def _clear_dir(path: str):
    """Remove all files in a directory (creates it if missing)."""
    os.makedirs(path, exist_ok=True)
    for f in os.listdir(path):
        fp = os.path.join(path, f)
        if os.path.isfile(fp):
            os.remove(fp)


def start_capture(source=0):
    os.makedirs("temp", exist_ok=True)
    _clear_dir("incidents")
    _clear_dir("temp_clips")

    # Tell connected frontends to clear stale alerts from any previous run
    try:
        httpx.post("https://sse.campusguard.tech/alerts/reset", timeout=2)
    except Exception:
        pass  # Server may not be up yet; frontend will reconnect fresh anyway

    # Initialize the threaded stream
    stream = CameraStream(source).start()

    executor = ThreadPoolExecutor(max_workers=5)
    clip_number = 0
    frames_buffer = []
    start_time = time.time()
    last_frame_time = 0.0
    CAPTURE_FPS = 15  # frames to collect per second
    FRAME_INTERVAL = 1.0 / CAPTURE_FPS  # ~67 ms between captured frames

    print("🎥 CCTV Started. Press Ctrl+C to stop.")

    try:
        while True:
            now = time.time()
            if now - last_frame_time < FRAME_INTERVAL:
                time.sleep(0.005)  # yield CPU, check again in 5 ms
                continue

            frame = stream.read()
            if frame is None:
                break

            last_frame_time = now
            frames_buffer.append(frame)
            elapsed_time = now - start_time

            if elapsed_time >= CLIP_DURATION:
                clip_number += 1

                executor.submit(
                    process_worker_single,
                    frames_buffer.copy(),
                    clip_number,
                    elapsed_time,
                )

                frames_buffer.clear()
                start_time = time.time()

    except KeyboardInterrupt:
        pass

    print("\nShutting down camera feed...")
    stream.stop()
    print("👋 System exited safely.")


if __name__ == "__main__":
    try:
        start_capture()
    except KeyboardInterrupt:
        print("\n🛑 CCTV System forced to shut down manually.")
