import os

with open("audio_manager.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add play_mode and loop logic to __init__
init_old = """    def __init__(self):
        self.active_playbacks = []
        self.focused_info = None
        self.playback_queue = []
        self.fade_in_ms = 0"""

init_new = """    def __init__(self):
        self.active_playbacks = []
        self.focused_info = None
        self.playback_queue = []
        self.play_mode = "overlay"  # "queue" or "overlay"
        self.fade_in_ms = 0"""
content = content.replace(init_old, init_new)

# 2. Update toggle_play_pause
toggle_old = """        if fi and (fi.get("is_paused") or (fi.get("device") and getattr(fi["device"], "running", False))):
            self.playback_queue.append({
                "filepath_primary": filepath_primary,
                "filepath_secondary": filepath_secondary,
                "name": name,
                "volume": volume,
                "primary_device_name": primary_device_name,
                "secondary_device_name": secondary_device_name,
                "dual_enabled": dual_enabled,
                "seek_offset": 0.0,
                "sound_id": sound_id
            })
            return

        self.stop_all()
        self.play_sound(filepath_primary, filepath_secondary, name, volume, primary_device_name, secondary_device_name, dual_enabled, 0.0, sound_id)"""

toggle_new = """        if fi and (fi.get("is_paused") or (fi.get("device") and getattr(fi["device"], "running", False))):
            if self.play_mode == "queue":
                self.playback_queue.append({
                    "filepath_primary": filepath_primary,
                    "filepath_secondary": filepath_secondary,
                    "name": name,
                    "volume": volume,
                    "primary_device_name": primary_device_name,
                    "secondary_device_name": secondary_device_name,
                    "dual_enabled": dual_enabled,
                    "seek_offset": 0.0,
                    "sound_id": sound_id
                })
                return
            elif self.play_mode == "overlay":
                # Do not stop_all, just play the new sound. It becomes the focused one.
                self.play_sound(filepath_primary, filepath_secondary, name, volume, primary_device_name, secondary_device_name, dual_enabled, 0.0, sound_id)
                return

        self.stop_all()
        self.play_sound(filepath_primary, filepath_secondary, name, volume, primary_device_name, secondary_device_name, dual_enabled, 0.0, sound_id)"""
content = content.replace(toggle_old, toggle_new)

with open("audio_manager.py", "w", encoding="utf-8") as f:
    f.write(content)

print("audio_manager.py toggle updated")
