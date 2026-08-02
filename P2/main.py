"""
main.py
Full pipeline: reel URL -> downloaded -> AI-described -> AI-written copy ->
framed into your channel template -> uploaded to YouTube Shorts.

Usage:
    python main.py "https://www.instagram.com/reel/xxxx/" [--frame frame.jpg] [--privacy public]
"""

import argparse
import os
import uuid

from pipeline.download import download_reel
from pipeline.generate_metadata import analyze_video, detect_crop
from pipeline.crop_video import extract_middle_frame, crop_video
from pipeline.apply_frame import apply_frame
from pipeline.upload import upload_short

OUTPUT_DIR = "final_outputs"


def run(reel_url: str, frame_path: str, privacy_status: str = "public", cookies_file: str | None = None):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_id = str(uuid.uuid4())[:8]

    print("\n=== Step 1/5: Downloading reel ===")
    reel = download_reel(reel_url, cookies_file)
    print(f"Downloaded: {reel['video_path']}")
    print(f"Original caption: {reel['description'][:100]}...")

    print("\n=== Step 2/5: Checking for baked-in border/watermark ===")
    frame_check_path = os.path.join(OUTPUT_DIR, f"{output_id}_check.png")
    extract_middle_frame(reel["video_path"], frame_check_path)
    crop_info = detect_crop(frame_check_path)
    print(f"Needs crop: {crop_info['needCrop']}")
    if crop_info["needCrop"]:
        print(f"Crop fractions: {crop_info['crop']}")

    video_to_frame = reel["video_path"]
    if crop_info.get("needCrop"):
        print("\n=== Step 2b: Cropping baked-in frame/watermark ===")
        cropped_path = os.path.join(OUTPUT_DIR, f"{output_id}_cropped.mp4")
        video_to_frame = crop_video(reel["video_path"], crop_info["crop"], cropped_path)
        print(f"Cropped: {video_to_frame}")

    print("\n=== Step 3/5: Writing title/description/hashtags with Gemini ===")
    copy = analyze_video(reel["video_path"], reel["description"])
    print(f"Title: {copy['title']}")
    print(f"Hashtags: {copy['hashtags']}")

    print("\n=== Step 4/5: Compositing into channel frame ===")
    final_video_path = os.path.join(OUTPUT_DIR, f"{output_id}.mp4")
    apply_frame(video_to_frame, frame_path, final_video_path)
    print(f"Framed video saved: {final_video_path}")

    print("\n=== Step 5/5: Uploading to YouTube Shorts ===")
    video_id = upload_short(
        video_path=final_video_path,
        title=copy["title"],
        description=copy["description"],
        tags=copy["hashtags"],
        privacy_status=privacy_status,
        made_for_kids=False,
    )

    print("\n=== DONE ===")
    print(f"https://youtube.com/shorts/{video_id}")
    return video_id


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reel -> YouTube Shorts pipeline")
    parser.add_argument("url", help="Instagram or Facebook reel URL")
    parser.add_argument("--frame", default="frame.jpg", help="Path to your channel frame template image")
    parser.add_argument("--privacy", default="public", choices=["public", "unlisted", "private"])
    parser.add_argument("--cookies", default=None, help="Path to cookies.txt if needed for IG auth")
    args = parser.parse_args()

    run(args.url, args.frame, args.privacy, args.cookies)
