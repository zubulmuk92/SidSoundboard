import json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "sounds": [],
    "language": "fr",
    "panic_hotkey": "None",
    "primary_output": None,
    "secondary_output": None,
    "dual_output_enabled": False,
    "global_secondary_volume": 100,
    "mode_solo": False,
    "fade_in_ms": 150,
    "fade_out_ms": 150,
}

# What the old "Atténuation (Ducking)" combo meant, as a volume to keep on
# the secondary output. The combo wrote a setting playback never read; the
# slider that replaced it writes global_secondary_volume directly.
_LEGACY_DUCKING_TO_VOLUME = {
    "Aucun": 100,
    "Léger (50%)": 50,
    "Fort (80%)": 20,
    "Total (100%)": 0,
}

SOUND_EFFECT_DEFAULTS = {
    "volume": 100,
    "speed": 100,
    "bass_boost": 0,
    "reverb": 0,
    "trim_start_sec": 0.0,
    "trim_end_sec": None,
    "cached_effects_file": None,
    "cached_secondary_file": None,
    "cached_secondary_volume": 100,
}


def migrate_settings(config):
    """
    Carries the old ducking combo over to the secondary-volume slider that
    replaced it. The combo's value was never read by playback, so this is
    the first time the choice actually takes effect.
    """
    legacy = config.pop("audio_ducking_level", None)
    if legacy is not None and "global_secondary_volume" not in config:
        config["global_secondary_volume"] = _LEGACY_DUCKING_TO_VOLUME.get(legacy, 100)
    return config


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
            # Legacy keys first: the default merge below would otherwise fill
            # in the new key and hide the old value we want to carry over.
            migrate_settings(cfg)
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
