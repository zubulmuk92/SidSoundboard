import sys
import os
import json
import subprocess
import threading

WORKER_FLAG = "--yt-worker"


def _build_subprocess_cmd(url, output_dir):
    if hasattr(sys, "_MEIPASS"):
        # Frozen build: sys.executable IS this app's own exe, re-launched
        # with a flag that makes it run only the worker and exit - no GUI,
        # no Qt, no miniaudio. This is how the yt_dlp import (and its ~25 Mo
        # of dependencies) stays entirely out of the main app's memory.
        return [sys.executable, WORKER_FLAG, url, output_dir]
    main_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
    return [sys.executable, main_script, WORKER_FLAG, url, output_dir]


def download_youtube_audio_async(url, output_dir, callback, progress_callback):
    def worker():
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            startupinfo = None
            if os.name == "nt":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            proc = subprocess.Popen(
                _build_subprocess_cmd(url, output_dir),
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace",
                startupinfo=startupinfo,
            )

            results = None
            error = None
            for line in proc.stdout:
                line = line.strip()
                if line.startswith("PROGRESS "):
                    try:
                        pct = int(line.split(" ", 1)[1])
                        progress_callback(f"{pct}%", None, None, "")
                    except (ValueError, IndexError):
                        pass
                elif line.startswith("DONE "):
                    results = json.loads(line.split(" ", 1)[1])
                elif line.startswith("ERROR "):
                    error = line.split(" ", 1)[1]

            proc.wait()

            if results is not None:
                callback(True, [(r["filepath"], r["title"]) for r in results], "")
            else:
                callback(False, None, error or "Échec du téléchargement")
        except Exception as e:
            callback(False, None, str(e))

    threading.Thread(target=worker, daemon=True).start()


def run_worker(url, output_dir):
    """Entry point executed only inside the isolated subprocess (see
    _build_subprocess_cmd). Only this function imports yt_dlp, so the
    heavy dependency tree never touches the main GUI process's memory,
    and is fully released back to the OS when this process exits."""
    import re
    import yt_dlp
    from audio_processor import normalize_and_import_audio

    def yt_progress_hook(d):
        if d["status"] == "downloading":
            downloaded = d.get("downloaded_bytes", 0)
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            if total > 0:
                pct = int((downloaded / total) * 100)
                print(f"PROGRESS {pct}", flush=True)

    try:
        if hasattr(sys, "_MEIPASS"):
            ffmpeg_loc = os.path.join(sys._MEIPASS, "bin", "win32")
        else:
            ffmpeg_loc = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin", "win32")

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "ffmpeg_location": ffmpeg_loc,
            "progress_hooks": [yt_progress_hook],
            "extractor_args": {"youtube": {"player_client": ["android"]}},
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            entries = info_dict["entries"] if "entries" in info_dict else [info_dict]

            results = []
            for entry in entries:
                if not entry:
                    continue
                file_path = ydl.prepare_filename(entry)
                title = entry.get("title", "Unknown")
                if os.path.exists(file_path):
                    final_path = normalize_and_import_audio(file_path, output_dir, title)
                    try:
                        os.remove(file_path)
                    except Exception:
                        pass
                    results.append({"filepath": final_path, "title": title})

            print(f"DONE {json.dumps(results)}", flush=True)
    except Exception as e:
        print(f"ERROR {str(e)}", flush=True)
