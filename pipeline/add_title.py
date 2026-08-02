from PIL import Image, ImageDraw, ImageFont
import os

TITLE_BOX_X = 130
TITLE_BOX_Y = 590

TITLE_BOX_W = 1467   
TITLE_BOX_H = 200

FONT_SIZE = 105
FONT_COLOR = (20, 20, 20) 


FONT_CANDIDATES = [
    "georgiab.ttf",
    "timesb.ttf",
    "C:/Windows/Fonts/georgiab.ttf",
    "C:/Windows/Fonts/timesb.ttf",
]


def _load_font(size: int):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    print("Warning: no serif font found, falling back to default (won't match header style).")
    return ImageFont.load_default()


def _wrap_text(text: str, font, max_width: int, draw: ImageDraw.Draw) -> list[str]:
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def add_title(frame_path: str, title_text: str, output_path: str) -> str:

    frame = Image.open(frame_path).convert("RGBA")
    draw = ImageDraw.Draw(frame)

    font = _load_font(FONT_SIZE)
    lines = _wrap_text(title_text, font, TITLE_BOX_W, draw)

    line_height = FONT_SIZE * 1.2
    while len(lines) * line_height > TITLE_BOX_H and font.size > 30:
        font = _load_font(font.size - 5)
        lines = _wrap_text(title_text, font, TITLE_BOX_W, draw)
        line_height = font.size * 1.2

    total_text_height = len(lines) * line_height
    start_y = TITLE_BOX_Y + (TITLE_BOX_H - total_text_height) / 2

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        x = TITLE_BOX_X
        y = start_y + i * line_height
        draw.text((x, y), line, font=font, fill=FONT_COLOR)

    frame.convert("RGB").save(output_path)
    return output_path


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: python add_title.py <frame_path> <title_text> <output_path>")
        sys.exit(1)

    result = add_title(sys.argv[1], sys.argv[2], sys.argv[3])
    print(f"Saved: {result}")


