import asyncio
import os
import time
import threading
import cv2 as cv
from gemini import analyze_clip

# --- CONFIGURATION ---
CLIP_DURATION = 10 

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

def write_video_to_disk_sync(frames, clip_path, fps, width, height):
    fourcc = cv.VideoWriter_fourcc(*"mp4v")
    safe_fps = max(1.0, float(fps))
    writer = cv.VideoWriter(clip_path, fourcc, safe_fps, (width, height))
    for frame in frames:
        writer.write(frame)
    writer.release()

async def process_and_analyze(frames, clip_number, duration, width, height):
    clip_path = f"videos/clip_{clip_number}.mp4"
    actual_fps = len(frames) / duration
    
    # 1. Threaded Disk Write
    await asyncio.to_thread(
        write_video_to_disk_sync, frames, clip_path, actual_fps, width, height
    )
    
    # 2. Async API Call
    try:
        print(f"🚀 [UPLOAD] Sending {clip_path} to Gemini...")
        result = await analyze_clip(clip_path)
        if result and result.get("is_fight"):
            print(f"🚨 ALERT: Fight detected in {clip_path}!")
        else:
            print(f"✅ Clear: {clip_path}. Removing.")
            if os.path.exists(clip_path):
                os.remove(clip_path)
    except Exception as e:
        print(f"❌ Error: {e}")

async def start_capture(source=0):
    os.makedirs("videos", exist_ok=True)
    
    # Initialize the threaded stream
    stream = CameraStream(source).start()
    
    # Pre-fetch resolution
    width = int(stream.cap.get(cv.CAP_PROP_FRAME_WIDTH))
    height = int(stream.cap.get(cv.CAP_PROP_FRAME_HEIGHT))

    clip_number = 0
    frames_buffer = []
    background_tasks = set()
    start_time = time.time()

    print("🎥 CCTV Started (Threaded). Press 'q' to stop.")

    while True:
        frame = stream.read()
        if frame is None:
            break

        frames_buffer.append(frame)
        elapsed_time = time.time() - start_time

        if elapsed_time >= CLIP_DURATION:
            clip_number += 1
            task = asyncio.create_task(
                process_and_analyze(frames_buffer.copy(), clip_number, elapsed_time, width, height)
            )
            background_tasks.add(task)
            task.add_done_callback(background_tasks.discard)

            frames_buffer.clear()
            start_time = time.time()

        # Display Live Feed
        cv.imshow("CCTV Feed", frame)
        
        # Give a micro-moment for the event loop
        await asyncio.sleep(0.001)

        if cv.waitKey(1) == ord("q"):
            break

    stream.stop()
    cv.destroyAllWindows()
    
    if background_tasks:
        print(f"⏳ Finishing {len(background_tasks)} uploads...")
        await asyncio.gather(*background_tasks, return_exceptions=True)

if __name__ == "__main__":
    try:
        asyncio.run(start_capture())
    except KeyboardInterrupt:
        print("\nShutdown.")