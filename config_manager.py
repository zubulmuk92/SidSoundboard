import json
import os

import paths
import profiles

# Bumped whenever the stored shape changes. A config without the key is
# version 1 — the shape that shipped before migrations were versioned.
#   1 -> 2  flat sound list becomes a profile, dead ducking key retired
#   2 -> 3  sounds still holding their path under the pre-rewrite `file`
#           key are recovered (they were invisible, audio intact on disk)
CONFIG_VERSION = 3

DEFAULT_CONFIG = {
    "config_version": CONFIG_VERSION,
    "profiles": [],
    "active_profile": None,
    "language": "fr",
    "panic_hotkey": "None",
    "primary_output": None,
    "secondary_output": None,
    "dual_output_enabled": False,
    "global_secondary_volume": 100,
    "master_volume": 100,
    "mode_solo": False,
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
    "loop": False,
    "cached_effects_file": None,
    "cached_secondary_file": None,
    "cached_secondary_volume": 100,
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


def _backfill_sounds(config):
    """
    Fills in the per-sound effect keys on sounds imported before the
    effects pipeline existed. Per-sound fades inherit whatever global
    values were in force, so nothing audibly changes on upgrade.
    """
    for sound in profiles.all_sounds(config):
        for key, value in SOUND_EFFECT_DEFAULTS.items():
            sound.setdefault(key, value)
        sound.setdefault("fade_in_ms", config.get("fade_in_ms", 150))
        sound.setdefault("fade_out_ms", config.get("fade_out_ms", 150))
    return config


# Keys a pre-rewrite version wrote, superseded by the current schema.
_LEGACY_SOUND_KEYS = ("cached_file", "cached_file_primary", "cached_file_secondary",
                      "device", "second_device", "audio_ducking")

# "Aucun" was an older unbound-hotkey sentinel; only "None" was ever filtered.
_LEGACY_HOTKEY_SENTINELS = ("Aucun", "aucun", "")


def _recover_legacy_sounds(config):
    """
    Rescues sounds written before the UI rewrite. They stored their path
    under `file`; the rewrite switched to `filename` and fixed the readers
    but never migrated the data, so those sounds have been silently
    invisible ever since — their audio files are still on disk.
    """
    for sound in profiles.all_sounds(config):
        if not sound.get("filename") and sound.get("file"):
            sound["filename"] = sound["file"]
        sound.pop("file", None)

        if sound.get("hotkey") in _LEGACY_HOTKEY_SENTINELS:
            sound["hotkey"] = "None"

        for key in _LEGACY_SOUND_KEYS:
            sound.pop(key, None)
    return config


def _drop_pathless_sounds(config):
    """Entries with no usable path at all cannot be played or repaired."""
    for profile in config.get("profiles", []):
        profile["sounds"] = [s for s in profile.get("sounds", []) if s.get("filename")]
    return config


def _absolutize_paths(config, base_dir):
    """
    Older configs stored `filename` relative to the working directory while
    `cached_effects_file` was absolute — so the library read as empty when
    the app started anywhere else. Relative paths are resolved against the
    folder the config came from, which is where those files actually are.
    """
    for sound in profiles.all_sounds(config):
        for key in ("filename", "cached_effects_file", "cached_secondary_file"):
            value = sound.get(key)
            if value and not os.path.isabs(value):
                sound[key] = os.path.abspath(os.path.join(base_dir, value))
    return config


def _migrate_v1_to_v2(config, base_dir):
    """
    v1 -> v2: the flat sound list becomes a single profile, the dead
    ducking combo becomes a real secondary volume, per-sound effect keys
    are backfilled, and every stored path becomes absolute.
    """
    legacy = config.pop("audio_ducking_level", None)
    if legacy is not None and "global_secondary_volume" not in config:
        config["global_secondary_volume"] = _LEGACY_DUCKING_TO_VOLUME.get(legacy, 100)

    config.pop("main_volume", None)  # never read by anything

    profiles.ensure_profiles(config)
    _backfill_sounds(config)
    _absolutize_paths(config, base_dir)


def _migrate_v2_to_v3(config, base_dir):
    """
    v2 -> v3: repairs sounds the UI rewrite left behind.

    This could not live in v1 -> v2: configs written by the first version
    that shipped profiles are already stamped 2, so a fix folded into that
    step would never run for them — which is exactly the case this
    migration exists to cover.
    """
    profiles.ensure_profiles(config)
    _recover_legacy_sounds(config)
    _drop_pathless_sounds(config)
    _backfill_sounds(config)
    _absolutize_paths(config, base_dir)


# (version the config is at or below, migration to run)
MIGRATIONS = [(1, _migrate_v1_to_v2), (2, _migrate_v2_to_v3)]


def migrate(config, base_dir=None):
    """Applies every migration the config has not seen yet, then stamps it."""
    if base_dir is None:
        base_dir = paths.data_dir()

    version = config.get("config_version", 1)
    for from_version, migration in MIGRATIONS:
        if version <= from_version:
            migration(config, base_dir)

    for key, value in DEFAULT_CONFIG.items():
        config.setdefault(key, value)

    profiles.ensure_profiles(config)
    config["config_version"] = CONFIG_VERSION
    return config


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_config():
    """
    Loads from the data folder, falling back once to the legacy location
    (the working directory) so an existing library is picked up after the
    upgrade. The legacy file is read, never moved: its sounds stay where
    they are, and are referenced by absolute path from then on.
    """
    path = paths.config_path()
    if os.path.exists(path):
        try:
            return migrate(_read(path), os.path.dirname(path))
        except (OSError, ValueError):
            return migrate(json.loads(json.dumps(DEFAULT_CONFIG)))

    legacy = paths.legacy_config_path()
    if os.path.exists(legacy) and os.path.abspath(legacy) != os.path.abspath(path):
        try:
            config = migrate(_read(legacy), os.path.dirname(legacy))
            save_config(config)
            return config
        except (OSError, ValueError):
            pass

    return migrate(json.loads(json.dumps(DEFAULT_CONFIG)))


def save_config(config):
    with open(paths.config_path(), "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
