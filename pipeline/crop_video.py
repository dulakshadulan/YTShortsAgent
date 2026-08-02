import subprocess
import json
import os


def get_video_dimensions(video_path: str) -> tuple[int, int]:
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "json",
        video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed:\n{result.stderr}")

    info = json.loads(result.stdout)
    stream = info["streams"][0]
    return stream["width"], stream["height"]


def crop_video(video_path: str, crop_fractions: dict, output_path: str) -> str:
    """
    crop_fractions: {"top": 0.05, "bottom": 0.05, "left": 0.0, "right": 0.0}
    Values are fractions (0.0-1.0) of the frame to cut from each edge.
    """
    width, height = get_video_dimensions(video_path)

    top = crop_fractions.get("top", 0.0)
    bottom = crop_fractions.get("bottom", 0.0)
    left = crop_fractions.get("left", 0.0)
    right = crop_fractions.get("right", 0.0)

    crop_w = int(width * (1 - left - right))
    crop_h = int(height * (1 - top - bottom))
    x_offset = int(width * left)
    y_offset = int(height * top)

    # Ensure even numbers (required for yuv420p encoding)
    crop_w -= crop_w % 2
    crop_h -= crop_h % 2

    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-vf", f"crop={crop_w}:{crop_h}:{x_offset}:{y_offset}",
        "-c:a", "copy",
        "-y",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg crop failed:\n{result.stderr}")

    return output_path


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python crop_video.py <video_path> <output_path> [top] [bottom] [left] [right]")
        sys.exit(1)

    video_path, output_path = sys.argv[1], sys.argv[2]
    fractions = {
        "top": float(sys.argv[3]) if len(sys.argv) > 3 else 0.0,
        "bottom": float(sys.argv[4]) if len(sys.argv) > 4 else 0.0,
        "left": float(sys.argv[5]) if len(sys.argv) > 5 else 0.0,
        "right": float(sys.argv[6]) if len(sys.argv) > 6 else 0.0,
    }
    result = crop_video(video_path, fractions, output_path)
    print(f"Cropped video saved: {result}")
