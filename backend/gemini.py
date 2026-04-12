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
            "enum": ["safe", "violent"],
        },
        "report": {"type": "STRING"},
    },
    "required": ["is_fight", "confidence", "severity", "report"],
}

PROMPT = """You are a school security CCTV monitoring AI. Analyze the video and determine if any physical altercation is occurring.

SAFE: People sitting, standing, walking, talking, studying, or having calm interactions.

VIOLENT: Any physical contact between people that resembles fighting, wrestling, punching,
shoving, grabbing, choking, or restraining — even if it appears playful or consensual.
A real security system cannot distinguish play-fighting from real fighting, so treat ALL
physical combat-like contact as violent.

If people are not touching each other or are just talking, it is SAFE.
If there is any physical contact that looks like fighting or wrestling, it is VIOLENT.

Do NOT assume violence when no physical contact is visible."""


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
