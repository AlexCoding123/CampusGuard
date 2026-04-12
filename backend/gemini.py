import json
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# Initialize client once at the module level
client = genai.Client()

# Define the structured schema
# This tells Gemini exactly what keys and types to return
ANALYSIS_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "is_fight": {"type": "BOOLEAN"},
        "confidence": {"type": "NUMBER"},
        "severity": {
            "type": "STRING",
            "enum": ["safe", "aggressive", "violent", "critical"],
        },
        "report": {"type": "STRING"},
    },
    "required": ["is_fight", "confidence", "severity", "report"],
}

PROMPT = """You are a school security CCTV monitoring AI. Your job is to ACCURATELY describe what is happening in the video.

IMPORTANT: Most clips will show NORMAL, safe activity (students sitting, walking, talking, studying).
Only flag something as a fight if you can clearly see physical contact with aggressive intent
(punching, kicking, shoving, choking, wrestling).

Do NOT hallucinate or assume violence. If people are just sitting, standing, or talking, that is SAFE.

SEVERITY LEVELS:
- safe: Normal activity — sitting, walking, talking, studying, standing around.
- aggressive: Clear pushing, shoving, or a fist fight.
- violent: Choking, head-kicking, or attacks likely to cause serious injury.
- critical: Use of weapons (knife, gun) or life-threatening assault.

Set is_fight to false and severity to "safe" unless you see CLEAR physical aggression."""


async def analyze_clip(clip_path: str):
    """Send a video clip to Gemini using structured output schema."""

    if not os.path.exists(clip_path):
        return {
            "is_fight": False,
            "confidence": 0.0,
            "severity": "safe",
            "report": "File not found.",
        }

    with open(clip_path, "rb") as f:
        video_bytes = f.read()

    try:
        # Note: model name might vary by tier, using flash for speed/cost
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=video_bytes, mime_type="video/mp4"),
                types.Part.from_text(text=PROMPT),
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ANALYSIS_SCHEMA,
                temperature=0.1,  # Low temperature for more consistent analysis
            ),
        )

        if response.text:
            return json.loads(response.text)

    except Exception as e:
        print(f"❌ Gemini API Error: {e}")

    return {
        "is_fight": False,
        "confidence": 0.0,
        "severity": "safe",
        "report": "Analysis encountered an error.",
    }
