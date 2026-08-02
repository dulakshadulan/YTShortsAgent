import argparse
import os
import uuid
from pathlib import Path

from pipeline.download import download_reel
from pipeline.generate_metadata import get_meta_data
from pipeline.crop_video import crop_video
from pipeline.apply_frame import apply_frame
from pipeline.upload import upload_short
from pipeline.add_title import add_title

CONFIG_DIR = Path("./.config")

OUTPUT_DIR = "final_outputs"
COOKIES = CONFIG_DIR / "cookies.txt"
VID_OUT = r".\outputs\output.mp4"
FRAME_OUT = r".\outputs\titled_frame.png"
FRAME_PATH = r".\src\frame.png"
FINAL_OUT = r".\outputs\final.mp4"


def run(reel_url: str ):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("\n=== Step 1/4: Downloading reel ===")
    reel = download_reel(reel_url, COOKIES)
    PATH = reel['video_path']
    JSON_PATH = reel['json_path']
    org_caption = reel['description']

    print(f"Downloaded: " , PATH)
    print(f"Original caption: {org_caption[:100]}...")

    print("\n=== Step 2/4: Getting metadata from Gemini ===")

    # data = {'dims': {'needCrop': True, 'crop': {'top': 0.266, 'bottom': 0.162, 'left': 0.0, 'right': 0.0}}, 'meta': {'title': 'Smells like victory.', 'description': "When hundreds of trailers unexpectedly parked on his ready-to-harvest field, this French farmer decided not to wait around for help. He hooked up his manure tanker and gave the uninvited guests a smell they won't soon forget. Turns out nothing clears a campsite faster than fresh liquid fertilizer!", 'hashtags': ['shorts', 'farmer', 'karma', 'funny', 'revenge'], 'category': 23}}

    data = get_meta_data(PATH,org_caption)
    dims = data['dims']
    meta = data['meta']
    print(data)
    meta['hashtags'] = meta['hashtags'] + [ 'funnyvideos', 'memepage', 'memecontent', 'internethumor','memes', 'funny', 'dankmemes', 'viral', 'fyp', 'foryou', 'foryoupage', 'viralvideo', 'relatable', 'comedy', 'funnyclip', 'lol', 'dailyhumor', 'internetmemes', 'usa', 'usashorts' ,'trending', 'explorepage', 'recommended', 'youtubeshorts', 'shorts', 'shortsvideo', 'shortsfeed', 'shortsviral']

    print("\n=== Step 3/4: Creating frame and cropping the video")
    CROPPED_VID = crop_video(PATH, dims['crop'], VID_OUT)
    TITLED_FRAME = add_title(FRAME_PATH, meta['title'], FRAME_OUT)
    FINAL_VIDEO = apply_frame(CROPPED_VID, TITLED_FRAME, FINAL_OUT)


    print("\n=== Step 4/4: Uploading to YouTube Shorts ===")

    video_id = upload_short(FINAL_VIDEO, meta['title'], meta['description'], meta['hashtags'],meta['category'] )

    os.remove(VID_OUT)
    os.remove(FRAME_OUT)
    os.remove(FINAL_OUT)
    os.remove("middle_frame.png")
    os.remove(PATH)
    os.remove(JSON_PATH)

    print("\n=== DONE ===")

    print(f"https://youtube.com/shorts/{video_id}")


if __name__ == "__main__":
        import sys
        if len(sys.argv) < 2:
            print("Usage: python crop_video.py <video_path> <output_path> [top] [bottom] [left] [right]")
            sys.exit(1)
        url = sys.argv[1]
        run(url)
    
