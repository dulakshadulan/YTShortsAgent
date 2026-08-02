"""
download.py
Downloads an Instagram Reel / Facebook Reel as an mp4 using yt-dlp.
"""

import subprocess
import uuid
import os
import json

DOWNLOAD_DIR = "downloads"


def download_reel(url: str, cookies_file: str | None = None) -> dict:

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    out_id = str(uuid.uuid4())[:8]
    out_template = os.path.join(DOWNLOAD_DIR, f"{out_id}.%(ext)s")

    cmd = [
        "yt-dlp",
        "-f", "bestvideo+bestaudio/best",
        "--merge-output-format", "mp4",
        "--write-info-json",
        "-o", out_template,
        url,
    ]

    if cookies_file:
        cmd.extend(["--cookies", cookies_file])

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp failed:\n{result.stderr}")

    expected_path = os.path.join(DOWNLOAD_DIR, f"{out_id}.mp4")
    if not os.path.exists(expected_path):
        matches = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith(".mp4") and f.startswith(out_id)]
        if not matches:
            raise RuntimeError("Download succeeded but output file not found.")
        expected_path = os.path.join(DOWNLOAD_DIR, matches[0])

    info_json_path = os.path.join(DOWNLOAD_DIR, f"{out_id}.info.json")
    caption, uploader, tags, title = "", "", [], ""
    if os.path.exists(info_json_path):
        with open(info_json_path, "r", encoding="utf-8") as f:
            info = json.load(f)
        caption = (info.get("description") or info.get("title") or "").strip()
        uploader = info.get("uploader", "")
        title = (info.get("title") or caption[:80]).strip()
        tags = [w.strip("#") for w in caption.split() if w.startswith("#")]

    return {
        "video_path": expected_path,
        "title": title,
        "description": caption,
        "uploader": uploader,
        "tags": tags,
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python download.py <reel_url> [cookies_file]")
        sys.exit(1)
    url = sys.argv[1]
    cookies = sys.argv[2] if len(sys.argv) > 2 else None
    result = download_reel(url, cookies)
    print(f"Downloaded to: {result['video_path']}")
    print(f"Original caption: {result['description']}")
    print(f"Uploader: {result['uploader']}")
    print(f"Tags found: {result['tags']}")
