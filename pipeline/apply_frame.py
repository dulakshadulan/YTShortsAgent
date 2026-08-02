"""
apply_frame.py
Overlays a downloaded reel video into a static frame template
(channel header stays fixed, video fills the placeholder box).

Uses a scale-to-fit + pad approach (no cropping) so vertical, horizontal,
or square videos all fit fully inside the box, centered, with no content
cut off. Padding color matches the frame's background so it blends in.
"""

import subprocess
import os

# Coordinates measured from the Daily Highlights frame (1701x3024).
# If you switch to a differently-sized/laid-out frame, re-measure these.
BOX_X = 60
BOX_Y = 800
BOX_W = 1580
BOX_H = 2180

# Matches the frame's background color so letterboxing blends in seamlessly.
PAD_COLOR = "0xF2F0EF"


def apply_frame(video_path: str, frame_path: str, output_path: str) -> str:
    """
    Composites `video_path` into the placeholder area of `frame_path`.
    The video is scaled to fit fully inside the box (no cropping), then
    centered, with any leftover space padded in the frame's background color.

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
        f"[1:v]scale={BOX_W}:{BOX_H}:force_original_aspect_ratio=decrease,"
        f"pad={BOX_W}:{BOX_H}:-1:-1:color={PAD_COLOR}[vid];"
        f"[0:v][vid]overlay={BOX_X}:{BOX_Y}:shortest=1,crop=trunc(iw/2)*2:trunc(ih/2)*2[out]"
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