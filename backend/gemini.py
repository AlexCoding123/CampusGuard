from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()


# Only for videos of size <20Mb
video_file_name = "./sample.mp4"
video_bytes = open(video_file_name, "rb").read()
client = genai.Client()
response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=types.Content(
        parts=[
            types.Part(inline_data=types.Blob(data=video_bytes, mime_type="video/mp4")),
            types.Part(text="Please summarize the video in 3 sentences."),
        ]
    ),
)
print(response.text)
