import os
import time
import threading
import queue
import asyncio
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
        clip_path = f"videos/clip_{clip_number}.mp4"
        actual_fps = len(frames) / duration
        
        print(f"📦 Packaging clip {clip_number} ({len(frames)} frames @ {actual_fps:.1f} FPS)...")
        
        # 1. Write to Disk (Blocks this thread, but UI/Camera doesn't care!)
        fourcc = cv.VideoWriter_fourcc(*"mp4v")
        safe_fps = min(60.0, max(1.0, float(actual_fps)))
        writer = cv.VideoWriter(clip_path, fourcc, safe_fps, (width, height))
        for frame in frames:
            writer.write(frame)
        writer.release()
        
        # 2. Send to Gemini
        print(f"🚀 [UPLOAD] Sending {clip_path} to Gemini...")
        try:
            # We use asyncio.run() here to safely execute your async Gemini function 
            # inside this synchronous worker thread.
            result = asyncio.run(analyze_clip(clip_path))
            
            report = result.get("report")
            if result.get("is_fight"):
                severity = result.get("severity")
                if severity == "critical":
                    print(f"🚨 {clip_path}: IMMEDIATE POLICE DISPATCH REQUIRED 🚨")
                    print(f"{report}\n")
                elif severity == "violent":
                    print(f"🚨 {clip_path}: CAMPUS SECURITY ALERT: HIGH PRIORITY 🚨")
                    print(f"{report}\n")
                else:
                    print(f"🚨 {clip_path}: altercation detected.")
                    print(f"{report}\n")
            else:
                print(f"✅ Clear: {clip_path}.")
                print(f"{report}\n")
        except Exception as e:
            print(f"❌ Error: {e}")
            
        job_queue.task_done()

def start_capture(source=0):
    os.makedirs("videos", exist_ok=True)
    
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
            job_queue.put((frames_buffer.copy(), clip_number, elapsed_time, width, height))
            
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
    
    job_queue.put(None) # Send the shutdown signal to the worker
    ai_thread.join()    # Wait for the worker to finish
    print("👋 System exited safely.")

if __name__ == "__main__":
    try:
        # Notice we don't need asyncio.run() here anymore!
        start_capture()
    except KeyboardInterrupt:
        print("\n🛑 CCTV System forced to shut down manually.")