"""
apply_frame.py
Overlays a downloaded reel video into a static frame template
(channel header stays fixed, video fills the placeholder box).

Uses a scale-up + center-crop approach (no padding) so the video
fills the box completely without stretching or squishing.
"""

import subprocess
import os

# Coordinates measured from the demo frame (720x1280).
# If you switch to a differently-sized frame image, re-measure these.
BOX_X = 15
BOX_Y = 315
BOX_W = 690
BOX_H = 920


def apply_frame(video_path: str, frame_path: str, output_path: str) -> str:
    """
    Composites `video_path` into the placeholder area of `frame_path`.
    The video is scaled up until it fully covers the box, then
    center-cropped to fit exactly (no black bars, no stretching).

    Args:
        video_path: path to the downloaded reel mp4.
        frame_path: path to the static frame template image (png/jpg).
        output_path: where to save the final composited mp4.

    Returns:
        output_path
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(video_path)
    if not os.path.exists(frame_path):
        raise FileNotFoundError(frame_path)

    filter_complex = (
        f"[1:v]scale={BOX_W}:{BOX_H}:force_original_aspect_ratio=increase,"
        f"crop={BOX_W}:{BOX_H}[vid];"
        f"[0:v][vid]overlay={BOX_X}:{BOX_Y}:shortest=1[out]"
    )

    cmd = [
        "ffmpeg",
        "-loop", "1", "-i", frame_path,
        "-i", video_path,
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-map", "1:a?",          # ? = don't fail if the source has no audio track
        "-c:v", "libx264",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        "-shortest",
        "-y",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{result.stderr}")

    return output_path


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: python apply_frame.py <video.mp4> <frame.png> <output.mp4>")
        sys.exit(1)
    out = apply_frame(sys.argv[1], sys.argv[2], sys.argv[3])
    print(f"Saved composited video to: {out}")
