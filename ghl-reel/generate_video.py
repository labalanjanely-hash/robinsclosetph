from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import re

# ─── CONFIG ───────────────────────────────────────────
WIDTH, HEIGHT = 1080, 1920       # Vertical/Reel format (9:16)
BG_COLOR      = (0, 0, 0)        # Black background
TEXT_COLOR    = (255, 255, 255)  # White text
FONT_SIZE     = 60
FPS           = 30
OUTPUT_FILE   = "GHL_Reel_Output.mp4"
SRT_FILE      = "GHL_Reel_Captions.srt"
# ──────────────────────────────────────────────────────


def parse_srt(filepath):
    """Parse SRT file and return list of (start, end, text) tuples in seconds."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(
        r"\d+\s+"
        r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s+-->\s+"
        r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s+"
        r"([\s\S]*?)(?=\n\n|\Z)",
        re.MULTILINE
    )

    captions = []
    for match in pattern.finditer(content):
        h1, m1, s1, ms1 = int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4))
        h2, m2, s2, ms2 = int(match.group(5)), int(match.group(6)), int(match.group(7)), int(match.group(8))
        start = h1*3600 + m1*60 + s1 + ms1/1000
        end   = h2*3600 + m2*60 + s2 + ms2/1000
        text  = match.group(9).strip()
        captions.append((start, end, text))

    return captions


def make_text_frame(text, width, height):
    """Create a numpy image frame with centered text."""
    img = Image.new("RGB", (width, height), color=BG_COLOR)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arialbd.ttf", FONT_SIZE)   # Bold Arial (Windows)
    except:
        try:
            font = ImageFont.truetype("Arial Bold.ttf", FONT_SIZE)  # macOS
        except:
            font = ImageFont.load_default()

    # Word-wrap text
    words = text.split()
    lines, line = [], ""
    for word in words:
        test = (line + " " + word).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= width - 80:
            line = test
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)

    # Draw each line centered
    total_height = sum(draw.textbbox((0,0), l, font=font)[3] for l in lines) + 10 * len(lines)
    y = (height - total_height) // 2

    for l in lines:
        bbox = draw.textbbox((0, 0), l, font=font)
        x = (width - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), l, font=font, fill=TEXT_COLOR)
        y += (bbox[3] - bbox[1]) + 10

    return np.array(img)


def main():
    captions = parse_srt(SRT_FILE)

    clips = []
    prev_end = 0

    for (start, end, text) in captions:
        # Add blank gap if needed
        if start > prev_end:
            blank = ColorClip(size=(WIDTH, HEIGHT), color=BG_COLOR, duration=start - prev_end)
            clips.append(blank)

        # Create text frame
        frame = make_text_frame(text, WIDTH, HEIGHT)
        clip = ImageClip(frame).set_duration(end - start)
        clips.append(clip)
        prev_end = end

    # Concatenate all clips
    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(OUTPUT_FILE, fps=FPS, codec="libx264", audio=False)
    print(f"\n✅ Done! Video saved as: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
