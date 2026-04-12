import asyncio
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import cv2 as cv
import imageio

from gemini import analyze_clip

import httpx
from datetime import datetime, timezone


# --- CONFIGURATION ---
CLIP_DURATION = 5


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


def process_worker_single(frames, clip_number, duration, width, height):
    """Process a single clip in its own thread."""
    temp_path = f"temp_clips/clip_{clip_number}.mp4"
    actual_fps = len(frames) / duration
    safe_fps = min(60.0, max(1.0, float(actual_fps)))

    os.makedirs("temp_clips", exist_ok=True)

    # Downscale to 640x480 for smaller files / faster Gemini upload.
    # Write H.264 via imageio-ffmpeg (bundles its own FFmpeg — no system
    # FFmpeg or openh264 DLL required). H.264 is required for Firefox/Vivaldi.
    small_w, small_h = 640, 480
    with imageio.get_writer(
        temp_path,
        fps=safe_fps,
        codec="libx264",
        output_params=["-pix_fmt", "yuv420p", "-crf", "23", "-preset", "fast"],
    ) as vid_writer:
        for frame in frames:
            small = cv.resize(frame, (small_w, small_h))
            vid_writer.append_data(small[:, :, ::-1])  # BGR → RGB

    print(f"🔍 Analyzing clip_{clip_number} ({len(frames)} frames)...")
    try:
        result = asyncio.run(analyze_clip(temp_path))

        report = result.get("report")
        severity = result.get("severity")
        if severity == "violent":
            os.makedirs("incidents", exist_ok=True)
            incident_path = f"incidents/clip_{clip_number}.mp4"
            os.rename(temp_path, incident_path)
            print(f"🚨 {incident_path}: VIOLENT — {report}\n")
            httpx.post("http://127.0.0.1:8080/alerts/send", json={
                "group_id": "1",
                "severity": result.get("severity"),
                "confidence": round(float(result.get("confidence", 0.5)), 2),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "location": "Camera 1 - Main Entrance",
                "video_url": f"http://127.0.0.1:8080/incidents/clip_{clip_number}.mp4",
                "report": result.get("report", ""),
            })
        else:
            os.remove(temp_path)
            print(f"✅ Clear: clip_{clip_number} — {report}\n")
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
        httpx.post("http://127.0.0.1:8080/alerts/reset", timeout=2)
    except Exception:
        pass  # Server may not be up yet; frontend will reconnect fresh anyway

    # Initialize the threaded stream
    stream = CameraStream(source).start()
    width = int(stream.cap.get(cv.CAP_PROP_FRAME_WIDTH))
    height = int(stream.cap.get(cv.CAP_PROP_FRAME_HEIGHT))

    executor = ThreadPoolExecutor(max_workers=5)
    clip_number = 0
    frames_buffer = []
    start_time = time.time()

    print("🎥 CCTV Started. Press 'q' to stop.")

    while True:
        frame = stream.read()
        if frame is None:
            break

        frames_buffer.append(frame)
        elapsed_time = time.time() - start_time

        if elapsed_time >= CLIP_DURATION:
            clip_number += 1

            executor.submit(
                process_worker_single,
                frames_buffer.copy(), clip_number, elapsed_time, width, height,
            )

            frames_buffer.clear()
            start_time = time.time()

        cv.imshow("CCTV Feed", frame)

        if cv.waitKey(33) == ord("q"):
            break

    print("\nShutting down camera feed...")
    stream.stop()
    cv.destroyAllWindows()
    print("👋 System exited safely.")


if __name__ == "__main__":
    try:
        start_capture()
    except KeyboardInterrupt:
        print("\n🛑 CCTV System forced to shut down manually.")
