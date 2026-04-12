import asyncio
import os
import queue
import subprocess
import threading
import time

import cv2 as cv

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


def reencode_h264(input_path: str, output_path: str) -> bool:
    """Re-encode to H.264 MP4 with faststart for browser compatibility."""
    try:
        result = subprocess.run(
            [
                "ffmpeg", "-y", "-i", input_path,
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                output_path,
            ],
            capture_output=True,
            timeout=120,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def process_worker(job_queue):
    """
    Background Worker Thread.
    It sits and waits for jobs, writes to disk, and calls Gemini.
    """
    while True:
        job = job_queue.get()
        if job is None:  # A "None" job is our signal to shut down
            break

        frames, clip_number, duration, width, height = job
        temp_path = f"temp_clips/clip_{clip_number}.mp4"
        actual_fps = len(frames) / duration

        print(
            f"📦 Packaging clip {clip_number} ({len(frames)} frames @ {actual_fps:.1f} FPS)..."
        )

        # 1. Write to temp directory for Gemini
        os.makedirs("temp_clips", exist_ok=True)
        fourcc = cv.VideoWriter_fourcc(*"mp4v")
        safe_fps = min(60.0, max(1.0, float(actual_fps)))
        writer = cv.VideoWriter(temp_path, fourcc, safe_fps, (width, height))
        for frame in frames:
            writer.write(frame)
        writer.release()

        # Re-encode to H.264 + faststart so browsers (Firefox, Vivaldi) can play it
        h264_path = temp_path.replace(".mp4", "_web.mp4")
        if reencode_h264(temp_path, h264_path):
            os.remove(temp_path)
            temp_path = h264_path
        else:
            print("⚠️  FFmpeg not found — video may not play in Firefox/Vivaldi")

        # 2. Send to Gemini
        print(f"🚀 [UPLOAD] Sending {temp_path} to Gemini...")
        try:
            result = asyncio.run(analyze_clip(temp_path))

            report = result.get("report")
            severity = result.get("severity")
            if severity == "violent":
                # Move to incidents folder
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

        job_queue.task_done()


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

    # Initialize the threaded stream
    stream = CameraStream(source).start()
    width = int(stream.cap.get(cv.CAP_PROP_FRAME_WIDTH))
    height = int(stream.cap.get(cv.CAP_PROP_FRAME_HEIGHT))

    # --- Start the AI Worker Thread ---
    job_queue = queue.Queue()
    ai_thread = threading.Thread(target=process_worker, args=(job_queue,), daemon=True)
    ai_thread.start()

    clip_number = 0
    frames_buffer = []
    start_time = time.time()

    print("🎥 CCTV Started (Producer/Consumer). Press 'q' to stop.")

    while True:
        frame = stream.read()
        if frame is None:
            break

        frames_buffer.append(frame)
        elapsed_time = time.time() - start_time

        if elapsed_time >= CLIP_DURATION:
            clip_number += 1

            # Instantly toss the data into the bucket and keep moving
            job_queue.put(
                (frames_buffer.copy(), clip_number, elapsed_time, width, height)
            )

            frames_buffer.clear()
            start_time = time.time()

        cv.imshow("CCTV Feed", frame)

        # waitKey(33) pauses the loop for ~33ms, capping us at ~30 FPS.
        # This stops the CPU from grabbing duplicate frames!
        if cv.waitKey(33) == ord("q"):
            break

    print("\nShutting down camera feed...")
    stream.stop()
    cv.destroyAllWindows()

    # Graceful Shutdown
    pending_jobs = job_queue.qsize()
    if pending_jobs > 0:
        print(f"⏳ Waiting for {pending_jobs} pending AI analyses to finish...")

    job_queue.put(None)  # Send the shutdown signal to the worker
    ai_thread.join()  # Wait for the worker to finish
    print("👋 System exited safely.")


if __name__ == "__main__":
    try:
        # Notice we don't need asyncio.run() here anymore!
        start_capture()
    except KeyboardInterrupt:
        print("\n🛑 CCTV System forced to shut down manually.")
