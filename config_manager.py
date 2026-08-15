import json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "sounds": [],
    "panic_key": "pause",
    "panic_hotkey": "None",
    "main_volume": 1.0,
    "primary_output": None,
    "secondary_output": None,
    "dual_output_enabled": False,
    "audio_ducking_level": "Léger (50%)",
    "fade_in_ms": 150,
    "fade_out_ms": 150,
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            # Merge with default to ensure all keys exist
            for k, v in DEFAULT_CONFIG.items():
                if k not in cfg:
                    cfg[k] = v
            return cfg
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
