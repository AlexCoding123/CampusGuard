import asyncio
import os

import cv2 as cv

from gemini import analyze_clip


def process_worker_single(frames, clip_number, duration, width, height):
    """
    Process a single clip headlessly.
    Writes frames to an MP4 and sends to Gemini for analysis.
    """
    if not frames:
        return None

    os.makedirs("temp_clips", exist_ok=True)
    temp_path = f"temp_clips/clip_{clip_number}.mp4"

    # Calculate FPS based on what we actually received from the phone
    actual_fps = len(frames) / duration if duration > 0 else 5.0

    # Downscale to 640x480 for faster upload/processing
    small_w, small_h = 640, 480
    fourcc = cv.VideoWriter_fourcc(*"mp4v")

    # On a headless VM, VideoWriter is purely CPU-based, which is fine
    writer = cv.VideoWriter(temp_path, fourcc, actual_fps, (small_w, small_h))

    for frame in frames:
        # We resize each frame to the target video size
        small = cv.resize(frame, (small_w, small_h))
        writer.write(small)
    writer.release()

    print(f"🔍 Analyzing clip_{clip_number}...")

    try:
        # Run the async Gemini call
        result = asyncio.run(analyze_clip(temp_path))

        severity = result.get("severity", "safe")
        report = result.get("report", "No report generated.")

        if severity in ["violent", "critical"]:
            os.makedirs("incidents", exist_ok=True)
            incident_path = f"incidents/clip_{clip_number}.mp4"
            os.rename(temp_path, incident_path)
            print(f"🚨 {incident_path}: {severity.upper()} — {report}\n")
        else:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            print(f"✅ Clear: clip_{clip_number} — {report}\n")

        # VERY IMPORTANT: Return the result so main.py can send it to the dashboard
        return result

    except Exception as e:
        print(f"❌ Gemini Analysis Error: {e}")
        return {"is_fight": False, "severity": "safe", "report": f"Error: {str(e)}"}
