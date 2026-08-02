"""
generate_metadata.py
Uses Google Gemini to watch a video (frames + audio) and generate
a YouTube-ready title, description, and hashtags.
"""

import os
import time
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image
import sys
import subprocess

load_dotenv()  # reads .env in the current working directory

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found. Add it to your .env file.")

client = genai.Client(api_key=API_KEY)

PROMPT_TEMPLATE = """
You are watching a short vertical video (a "Reel" being repurposed for YouTube Shorts).
Watch it carefully, including any audio, speech, on-screen text, and music/sound context.

Here is the ORIGINAL caption/hashtags from the source post (may be empty or messy):
---
{original_caption}
---

Write YouTube Shorts copy based on what's actually happening in the video
(use the original caption for extra context, but don't just copy it verbatim).
Write copy that would make someone stop scrolling — natural, human, joyful tone,
not robotic, not generic, no overused phrases like "you won't believe what happens" and no emojy.
title should be short and be like a some kind of quote that makes interest to watch.
Few examples - Its the look on his face , dad joke award for today goes to , Okay : you can go now, technologia , His first betrayal , like some playful words like you are experiencing the event.
Can be one or multiple words.Its ok to use sarcasm, irony but not all the time use where it makes sense.
Also give the hashtages that will help the short to go viral . Use internet to find best metadata.

Return ONLY a JSON object (no markdown, no code fences, no extra text):
{{
  "title": "under 40 characters, catchy, specific to this content, joyful tone",
  "description": "2-4 sentences, natural human tone, not a dry summary",
  "hashtags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}

Hashtags: lowercase, no # symbol, relevant to actual content, include "shorts" as one.
"""


CROP_DETECTION_PROMPT = """
You are looking at a single frame from a vertical video (a "Reel" being repurposed
for YouTube Shorts).

Check if this frame has a baked-in border/frame/Caption-bar around the
actual footage. If so, we need to crop it out. The frame border can be white / black any color around the content. 
Try to find the exact point where need to crop the borders.


IMPORTANT: Check EACH edge (top, bottom, left, right) INDEPENDENTLY. Do NOT assume
they are symmetric. A bar at the top does NOT mean there's a matching bar at the
bottom — many frames only have something on ONE edge, or two adjacent edges, not
all four. Look at each edge separately.

Return ONLY a JSON object (no markdown, no code fences, no extra text):
{
  "needCrop": true,
  "crop": {
    "top": 0.0,
    "bottom": 0.0,
    "left": 0.0,
    "right": 0.0
  }
}

Values are fractions (0.0 to 1.0) of the frame's height/width to cut from each edge.
If needCrop is false, still include "crop" with all values 0.0.
"""


def get_video_duration(video_path: str) -> float:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed:\n{result.stderr}")
    return float(json.loads(result.stdout)["format"]["duration"])


def extract_middle_frame(video_path: str, output_path: str = "middle_frame.png") -> str:
    """
    Grabs a single frame from the exact middle of the video.
    Used for crop/border detection, which doesn't need the full video.
    """
    duration = get_video_duration(video_path)
    midpoint = duration / 2

    cmd = [
        "ffmpeg",
        "-ss", str(midpoint),
        "-i", video_path,
        "-frames:v", "1",
        "-y",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg frame extraction failed:\n{result.stderr}")

    return output_path

def detect_crop(frame_path: str) -> dict:
    """
    Sends a single frame (not the full video) to Gemini to detect any
    baked-in border/watermark/caption bar that needs cropping.
    Much cheaper and just as accurate as using the full video for this,
    since the border position doesn't change across frames.
    """
    from PIL import Image

    img = Image.open(frame_path)

    response = client.models.generate_content(
        # gemini-2.5-flash
        model="gemini-flash-latest",
        contents=[img, CROP_DETECTION_PROMPT],
    )

    text = response.text.strip().replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise RuntimeError(f"Could not parse Gemini's crop response as JSON:\n{text}")


def analyze_video(video_path: str, original_caption: str = "") -> dict:
    """
    Uploads video_path to Gemini and returns a dict with:
      title, description, hashtags, needCrop, crop (top/bottom/left/right fractions)
    based on both the video content AND the original source caption.
    """
    print("Uploading video to Gemini...")
    uploaded_file = client.files.upload(file=video_path)

    while uploaded_file.state.name == "PROCESSING":
        print("Processing...")
        time.sleep(3)
        uploaded_file = client.files.get(name=uploaded_file.name)

    if uploaded_file.state.name == "FAILED":
        raise RuntimeError("Gemini failed to process the uploaded video.")

    print("Analyzing video...")
    prompt = PROMPT_TEMPLATE.format(original_caption=original_caption or "(none provided)")

    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=[uploaded_file, prompt],
    )

    text = response.text.strip().replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        raise RuntimeError(f"Could not parse Gemini's response as JSON:\n{text}")

    return data


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python generate_metadata.py <video_path> [original_caption]")
        sys.exit(1)

    caption = sys.argv[2] if len(sys.argv) > 2 else ""
    result = analyze_video(sys.argv[1], caption)
    frame_path = extract_middle_frame(sys.argv[1], "check_frame.png")
    dims = detect_crop(frame_path)
    print(json.dumps(result, indent=2))
    print(dims)
