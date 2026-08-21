import yt_dlp
import sys

def yt_progress_hook(d):
    if d["status"] == "downloading":
        downloaded = d.get("downloaded_bytes", 0)
        total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
        if total > 0:
            pct = int((downloaded / total) * 100)
            print(f"PROGRESS {pct}", flush=True)

ydl_opts = {
    "format": "bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "noprogress": True,
    "progress_hooks": [yt_progress_hook],
    "extractor_args": {"youtube": {"player_client": ["android"]}},
}

try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info("https://www.youtube.com/watch?v=dQw4w9WgXcQ", download=True)
except Exception as e:
    print(f"ERROR: {e}")
