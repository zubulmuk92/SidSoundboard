import yt_dlp
import re
import sys

def yt_progress_hook(d):
    if d["status"] == "downloading":
        percent_str = d.get("_percent_str", "0%").strip()
        print(f"RAW: {percent_str!r}")
        percent_str = re.sub(r"\x1b[^m]*m", "", percent_str).replace("%", "").strip()
        try:
            print(f"PROGRESS {int(float(percent_str))}", flush=True)
        except ValueError as e:
            print(f"ValueError: {e}")

ydl_opts = {
    "format": "bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "progress_hooks": [yt_progress_hook],
    "extractor_args": {"youtube": {"player_client": ["android"]}},
}

try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info("https://www.youtube.com/watch?v=dQw4w9WgXcQ", download=True)
except Exception as e:
    print(f"ERROR: {e}")
