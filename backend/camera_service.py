import asyncio
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import cv2 as cv

from gemini import analyze_clip

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

    os.makedirs("temp_clips", exist_ok=True)
    # Downscale to 640x480 for smaller files / faster upload
    small_w, small_h = 640, 480
    fourcc = cv.VideoWriter_fourcc(*"mp4v")
    safe_fps = min(60.0, max(1.0, float(actual_fps)))
    writer = cv.VideoWriter(temp_path, fourcc, safe_fps, (small_w, small_h))
    for frame in frames:
        small = cv.resize(frame, (small_w, small_h))
        writer.write(small)
    writer.release()

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
        else:
            os.remove(temp_path)
            print(f"✅ Clear: clip_{clip_number} — {report}\n")
    except Exception as e:
        print(f"❌ Error: {e}")


def start_capture(source=0):
    os.makedirs("videos", exist_ok=True)

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
        # Notice we don't need asyncio.run() here anymore!
        start_capture()
    except KeyboardInterrupt:
        print("\n🛑 CCTV System forced to shut down manually.")
