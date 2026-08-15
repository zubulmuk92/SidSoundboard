import json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "sounds": [],
    "panic_hotkey": "None",
    "main_volume": 1.0,
    "primary_output": None,
    "secondary_output": None,
    "dual_output_enabled": False,
    "audio_ducking_level": "Léger (50%)",
    "fade_in_ms": 150,
    "fade_out_ms": 150,
}

SOUND_EFFECT_DEFAULTS = {
    "volume": 100,
    "speed": 100,
    "bass_boost": 0,
    "reverb": 0,
    "trim_start_sec": 0.0,
    "trim_end_sec": None,
    "cached_effects_file": None,
}


def migrate_sounds(config):
    """
    Backfills the per-sound effect keys on sounds imported before the
    effects pipeline existed. Per-sound fades inherit whatever global
    values were in force, so nothing audibly changes on upgrade.
    """
    for sound in config.get("sounds", []):
        for key, value in SOUND_EFFECT_DEFAULTS.items():
            sound.setdefault(key, value)
        sound.setdefault("fade_in_ms", config.get("fade_in_ms", 150))
        sound.setdefault("fade_out_ms", config.get("fade_out_ms", 150))
    return config


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return migrate_sounds(DEFAULT_CONFIG.copy())
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            # Merge with default to ensure all keys exist
            for k, v in DEFAULT_CONFIG.items():
                if k not in cfg:
                    cfg[k] = v
            return migrate_sounds(cfg)
    except Exception:
        return migrate_sounds(DEFAULT_CONFIG.copy())

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
