import os
import threading
import time
from datetime import datetime, timezone

import cv2 as cv
import httpx
import imageio
from gemini import analyze_frames

# --- INCIDENT GROUP TRACKING ---
_group_id           = 0
_incident_active    = False
_last_clip_time     = 0.0
_last_severity_sent = None
_group_lock         = threading.Lock()

SEVERITY_RANK = {"aggressive": 1, "critical": 2}
COOLDOWN      = 30  # seconds before the same severity can fire again


def _resolve_group(severity: str) -> str | None:
    """
    Decide whether to save and send a clip.
    Returns a group_id string if we should send, or None if we should drop it.
    """
    global _group_id, _incident_active, _last_clip_time, _last_severity_sent
    
    with _group_lock:
        if severity == "safe":
            _incident_active    = False
            _last_severity_sent = None
            return None

        now = time.time()
        if not _incident_active:
            # New incident started
            _group_id           += 1
            _incident_active     = True
            _last_clip_time      = now
            _last_severity_sent  = severity
            return str(_group_id)

        # Check for escalation (e.g., aggressive -> critical)
        current_rank = SEVERITY_RANK.get(severity, 0)
        last_rank = SEVERITY_RANK.get(_last_severity_sent or "", 0)
        
        is_escalation   = current_rank > last_rank
        cooldown_passed = (now - _last_clip_time) >= COOLDOWN

        if is_escalation or cooldown_passed:
            _last_clip_time     = now
            _last_severity_sent = severity
            return str(_group_id)

        return None  # Same severity within cooldown — block it


def process_worker_single(frames, clip_number, duration):
    """
    Process a single clip in its own thread (Headless Safe).
    
    Fast path: send raw frames to Gemini.
    Only encode H.264 when the clip is violent — safe clips are
    discarded immediately, saving time and disk I/O.
    """
    if not frames:
        return None

    actual_fps = len(frames) / duration if duration > 0 else 5.0
    print(f"🔍 Analyzing clip_{clip_number} ({len(frames)} frames @ {actual_fps:.1f} FPS)...")
    
    try:
        # Assuming analyze_frames is synchronous. If it's async, wrap in asyncio.run()
        result = analyze_frames(frames)

        severity = result.get("severity", "safe")
        report   = result.get("report", "No report generated.")

        group_id = _resolve_group(severity)

        if group_id is not None:
            # 🚨 VIOLENT CLIP - Encode and save
            os.makedirs("incidents", exist_ok=True)
            incident_path = f"incidents/clip_{clip_number}.mp4"
            
            safe_fps = min(60.0, max(1.0, float(actual_fps)))
            
            # Headless encoding using imageio (bypasses OpenCV UI dependencies)
            with imageio.get_writer(
                incident_path,
                fps=safe_fps,
                codec="libx264",
                output_params=["-pix_fmt", "yuv420p", "-crf", "23", "-preset", "fast"],
            ) as vid_writer:
                for frame in frames:
                    # Resize to 720x544 and convert OpenCV's BGR format to standard RGB
                    small = cv.resize(frame, (720, 544))
                    vid_writer.append_data(small[:, :, ::-1])

            print(f"🚨 {incident_path}: {severity.upper()} (group {group_id}) — {report}\n")
            
            # Push alert to the local FastAPI server
            try:
                httpx.post("http://127.0.0.1:8080/alerts/send", json={
                    "group_id": group_id,
                    "severity": severity,
                    "confidence": round(float(result.get("confidence", 0.5)), 2),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "location": "Camera 1 - Main Entrance",
                    "video_url": f"http://127.0.0.1:8080/incidents/clip_{clip_number}.mp4",
                    "report": report,
                }, timeout=5.0)
            except Exception as http_err:
                print(f"⚠️ Failed to send alert via HTTP: {http_err}")

        else:
            # ✅ SAFE CLIP - Discard immediately
            print(f"✅ Clear: clip_{clip_number} — incident closed/ignored\n")

        return result

    except Exception as e:
        print(f"❌ Worker Error: {e}")
        return None


def clear_incident_dirs():
    """Utility to wipe directories on startup. Import and run this in main.py."""
    directories = ["incidents", "temp_clips", "temp"]
    for d in directories:
        os.makedirs(d, exist_ok=True)
        for f in os.listdir(d):
            fp = os.path.join(d, f)
            if os.path.isfile(fp):
                os.remove(fp)