import os
import glob
import config_manager

# Cache families this module owns and is free to delete when orphaned.
CACHE_PATTERNS = ("*_v*_s*.*", "*_fx.wav", "*_fx.wav.peaks.json", "*_sec.wav")

# Preview renders are throwaway by construction: never protected.
DISPOSABLE_PATTERNS = ("*_preview.wav", "*_preview.wav.peaks.json")


def cleanup_caches(config=None):
    """
    Deletes cache files that no sound in the config refers to any more:
    the per-sound effects renders (_fx), their peaks, the on-the-fly
    ducking renders (_v*_s*), and every leftover preview render.
    """
    if config is None:
        config = config_manager.load_config()

    active_files = set()
    for sound in config.get("sounds", []):
        for key in ("filename", "cached_effects_file", "cached_secondary_file"):
            path = sound.get(key)
            if not path:
                continue
            abs_path = os.path.abspath(path)
            active_files.add(abs_path)
            active_files.add(abs_path + ".peaks.json")

    search_dirs = {os.path.abspath("."), os.path.abspath("downloads")}
    for f in active_files:
        search_dirs.add(os.path.dirname(f))

    for d in search_dirs:
        if not os.path.isdir(d):
            continue
        for pattern in CACHE_PATTERNS:
            for f in glob.glob(os.path.join(d, pattern)):
                abs_f = os.path.abspath(f)
                if abs_f not in active_files:
                    _remove(abs_f)
        for pattern in DISPOSABLE_PATTERNS:
            for f in glob.glob(os.path.join(d, pattern)):
                _remove(os.path.abspath(f))


def _remove(path):
    try:
        os.remove(path)
    except OSError:
        pass
