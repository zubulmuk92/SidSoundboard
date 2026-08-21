import yt_dlp
import sys

ydl_opts = {
    "format": "bestaudio/best",
    "extractor_args": {"youtube": {"player_client": ["android"]}},
}

try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info("https://www.youtube.com/watch?v=dQw4w9WgXcQ", download=False)
    print("SUCCESS with dict of dict")
except Exception as e:
    print(f"ERROR: {e}")
