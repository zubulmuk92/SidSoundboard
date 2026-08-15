"""
Sound profiles.

A flat library stops being useful as it grows: a game, a stream and a
private call do not want the same sounds, nor the same keys bound. Sounds
therefore live in profiles, and only the active one is visible and bound.

Nothing outside this module touches config["profiles"] directly — the
whole point is that the rest of the app keeps working on a plain list of
sounds.
"""

import uuid

DEFAULT_PROFILE_NAME = "Général"


def _new_id():
    return uuid.uuid4().hex[:8]


def ensure_profiles(config):
    """Guarantees the config has at least one profile and a valid active
    one. Safe to call on any config, including a freshly migrated one."""
    profiles = config.get("profiles")
    if not profiles:
        profiles = [{
            "id": _new_id(),
            "name": DEFAULT_PROFILE_NAME,
            "sounds": config.pop("sounds", []) or [],
        }]
        config["profiles"] = profiles

    ids = {p["id"] for p in profiles}
    if config.get("active_profile") not in ids:
        config["active_profile"] = profiles[0]["id"]
    return config


def active_profile(config):
    ensure_profiles(config)
    active_id = config["active_profile"]
    for profile in config["profiles"]:
        if profile["id"] == active_id:
            return profile
    return config["profiles"][0]


def active_sounds(config):
    """The live list backing the active profile — mutating it mutates the
    config, which is what every caller expects."""
    return active_profile(config).setdefault("sounds", [])


def all_sounds(config):
    """Every sound across every profile. Cache cleanup needs this: sweeping
    on the active profile alone would delete the other profiles' renders."""
    ensure_profiles(config)
    return [s for p in config["profiles"] for s in p.get("sounds", [])]


def set_active(config, profile_id):
    ensure_profiles(config)
    if any(p["id"] == profile_id for p in config["profiles"]):
        config["active_profile"] = profile_id
    return config["active_profile"]


def create_profile(config, name):
    ensure_profiles(config)
    profile = {"id": _new_id(), "name": name or DEFAULT_PROFILE_NAME, "sounds": []}
    config["profiles"].append(profile)
    return profile


def rename_profile(config, profile_id, name):
    ensure_profiles(config)
    if not name:
        return
    for profile in config["profiles"]:
        if profile["id"] == profile_id:
            profile["name"] = name
            return


def delete_profile(config, profile_id):
    """Refuses to remove the last profile: there would be nowhere to put
    sounds, and no valid active profile. Returns True if it deleted one."""
    ensure_profiles(config)
    if len(config["profiles"]) <= 1:
        return False

    remaining = [p for p in config["profiles"] if p["id"] != profile_id]
    if len(remaining) == len(config["profiles"]):
        return False

    config["profiles"] = remaining
    if config.get("active_profile") == profile_id:
        config["active_profile"] = remaining[0]["id"]
    return True
