import subprocess
import os

# Frame dims =  (1701x3024).

BOX_X = 60
BOX_Y = 800
BOX_W = 1580
BOX_H = 2180

PAD_COLOR = "0xF2F0EF"


def apply_frame(video_path: str, frame_path: str, output_path: str) -> str:

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