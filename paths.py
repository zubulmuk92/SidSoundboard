"""
Where the application keeps its data.

Everything used to be relative to the current working directory, so a
shortcut with the wrong "Start in", or the app installed under Program
Files, silently opened an empty library. Data now lives next to the
executable when that folder can be written to — the app stays portable —
and falls back to %APPDATA% when it cannot.
"""

import os
import sys

APP_NAME = "SidSoundboard"

_data_dir = None


def app_dir():
    """The folder the app ships in: next to the .exe once frozen, the
    project root when running from source."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def _is_writable(directory):
    """Actually writes a file. Windows inherited ACLs make permission bits
    an unreliable answer, and virtualisation can fake a success on read."""
    probe = os.path.join(directory, f".{APP_NAME}.write-test")
    try:
        os.makedirs(directory, exist_ok=True)
        with open(probe, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(probe)
        return True
    except OSError:
        return False


def data_dir():
    """The folder holding config, sounds and logs. Resolved once."""
    global _data_dir
    if _data_dir is None:
        candidate = app_dir()
        if not _is_writable(candidate):
            candidate = os.path.join(
                os.environ.get("APPDATA") or os.path.expanduser("~"), APP_NAME
            )
            os.makedirs(candidate, exist_ok=True)
        _data_dir = candidate
    return _data_dir


def set_data_dir(directory):
    """Overrides the resolved folder. For tests."""
    global _data_dir
    _data_dir = directory


def config_path():
    return os.path.join(data_dir(), "config.json")


def downloads_dir():
    directory = os.path.join(data_dir(), "downloads")
    os.makedirs(directory, exist_ok=True)
    return directory


def log_path(name):
    return os.path.join(data_dir(), name)


def legacy_config_path():
    """Where older versions wrote their config: the working directory. Kept
    so an existing library can be picked up on first run after upgrading."""
    return os.path.abspath("config.json")
