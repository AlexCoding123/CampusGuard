import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

PROMPT = """You are a school security CCTV monitoring system. Analyze this video clip and determine if a physical fight or altercation is happening.

Respond in this exact JSON format:
{
  "is_fight": true or false,
  "confidence": 0.0 to 1.0,
  "report": "If a fight is detected, write a brief incident report describing the individuals involved (clothing, actions, setting). If no fight, write 'No incident detected.'"
}

Only respond with the JSON, nothing else."""


def analyze_clip(clip_path: str) -> dict:
    """Send a video clip to Gemini and return fight analysis."""
    with open(clip_path, "rb") as f:
        video_bytes = f.read()

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(
                data=video_bytes,
                mime_type="video/mp4",
            ),
            PROMPT,
        ],
    )

    # Parse the JSON response
    import json
    print(f"Gemini raw response: {response.text}")
    try:
        result = json.loads(response.text)
    except json.JSONDecodeError:
        result = {"is_fight": False, "confidence": 0.0, "report": "Analysis failed."}

    return result
