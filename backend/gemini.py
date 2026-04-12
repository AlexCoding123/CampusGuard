import json
import os

import cv2 as cv
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client()

ANALYSIS_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "severity": {
            "type": "STRING",
            "enum": ["safe", "aggressive", "critical"],
        },
        "confidence": {"type": "NUMBER"},
        "report":     {"type": "STRING"},
    },
    "required": ["severity", "confidence", "report"],
}

PROMPT = """You are a school security CCTV AI. Analyze these frames and classify the threat level. Err on the side of caution.

SAFE: Calm activity — walking, sitting, talking, studying. No physical tension or threat.

AGGRESSIVE: Any physical confrontation or threat —
- Raised fists, fighting stance, or squaring up toward another person
- Pushing, shoving, punching, kicking, slapping, or striking
- Wrestling, grabbing, choking, or restraining
- One person charging or lunging at another
- Simulated or mimicked fighting (treat the same as real fighting)
- Any sustained physical struggle between people

CRITICAL: Severe threat requiring immediate response — classify as CRITICAL if ANY of these appear in even ONE frame:
- A person lying, falling, collapsed, or pinned on the floor/ground
- Multiple attackers on one person
- Visible weapon or object used as a weapon
- One person completely overpowering another with no resistance
- Bystanders visibly fleeing in panic

When in doubt between SAFE and AGGRESSIVE, choose AGGRESSIVE.
When in doubt between AGGRESSIVE and CRITICAL, choose CRITICAL.

Return severity (safe/aggressive/critical), confidence (0-1), and a one-sentence report."""


def analyze_frames(frames: list) -> dict:
    """Analyze raw OpenCV (BGR) frames directly — no video file needed.

    Synchronous so it can be called safely from ThreadPoolExecutor threads
    without event-loop conflicts. Samples up to 5 evenly-spaced key frames,
    encodes each as JPEG, and sends them as images. Images are ~10x smaller
    than an H.264 clip and Gemini processes them significantly faster.
    """
    if not frames:
        return {"severity": "safe", "confidence": 0.0, "report": "No frames."}

    # Pick up to 8 evenly-spaced frames — more frames = fewer missed moments
    # (e.g. victim falling to ground near end of clip)
    n       = min(8, len(frames))
    step    = max(1, (len(frames) - 1) // max(n - 1, 1))
    indices = [min(i * step, len(frames) - 1) for i in range(n)]

    contents = []
    for idx in indices:
        _, jpg = cv.imencode(".jpg", frames[idx], [cv.IMWRITE_JPEG_QUALITY, 75])
        contents.append(
            types.Part.from_bytes(data=jpg.tobytes(), mime_type="image/jpeg")
        )
    contents.append(types.Part.from_text(text=PROMPT))

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ANALYSIS_SCHEMA,
                temperature=0.1,
            ),
        )
        if response.text:
            return json.loads(response.text)
    except Exception as e:
        print(f"❌ Gemini error: {e}")

    return {"severity": "safe", "confidence": 0.0, "report": "Analysis error."}


def analyze_clip(clip_path: str) -> dict:
    """Backward-compatible wrapper: extract frames from a video file and analyze."""
    if not os.path.exists(clip_path):
        return {"severity": "safe", "confidence": 0.0, "report": "File not found."}

    cap    = cv.VideoCapture(clip_path)
    total  = int(cap.get(cv.CAP_PROP_FRAME_COUNT))
    frames = []
    for i in range(5):
        cap.set(cv.CAP_PROP_POS_FRAMES, int(i * total / 5))
        ret, frame = cap.read()
        if ret:
            frames.append(frame)
    cap.release()

    return analyze_frames(frames)
