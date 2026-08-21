import os

# 1. Patch audio_manager.py
with open("audio_manager.py", "r", encoding="utf-8") as f:
    am_content = f.read()

am_content = am_content.replace(
    "def play_sound(self, filepath_primary, filepath_secondary, name, volume=1.0, primary_device_name=None, secondary_device_name=None, dual_enabled=False, seek_offset=0.0, sound_id=None):",
    "def play_sound(self, filepath_primary, filepath_secondary, name, volume=1.0, primary_device_name=None, secondary_device_name=None, dual_enabled=False, seek_offset=0.0, sound_id=None, loop=False):"
)
am_content = am_content.replace(
    """        self.focused_info = {
            "name": name,
            "filepath_primary": filepath_primary,
            "filepath_secondary": filepath_secondary,
            "primary_device_name": primary_device_name,
            "secondary_device_name": secondary_device_name,
            "dual_enabled": dual_enabled,
            "device": dev1,
            "fade_state": fade_state1,
            "duration": duration,
            "start_sys_time": time.time() - seek_offset,
            "seek_offset": seek_offset,
            "sound_id": sound_id,
            "is_paused": False
        }""",
    """        self.focused_info = {
            "name": name,
            "filepath_primary": filepath_primary,
            "filepath_secondary": filepath_secondary,
            "primary_device_name": primary_device_name,
            "secondary_device_name": secondary_device_name,
            "dual_enabled": dual_enabled,
            "device": dev1,
            "fade_state": fade_state1,
            "duration": duration,
            "start_sys_time": time.time() - seek_offset,
            "seek_offset": seek_offset,
            "sound_id": sound_id,
            "is_paused": False,
            "loop": loop
        }"""
)
am_content = am_content.replace(
    "def toggle_play_pause(self, filepath_primary, filepath_secondary, name, volume=1.0, primary_device_name=None, secondary_device_name=None, dual_enabled=False, sound_id=None):",
    "def toggle_play_pause(self, filepath_primary, filepath_secondary, name, volume=1.0, primary_device_name=None, secondary_device_name=None, dual_enabled=False, sound_id=None, loop=False):"
)
am_content = am_content.replace(
    "self.play_sound(filepath_primary, filepath_secondary, name, volume, primary_device_name, secondary_device_name, dual_enabled, seek, sound_id)",
    "self.play_sound(filepath_primary, filepath_secondary, name, volume, primary_device_name, secondary_device_name, dual_enabled, seek, sound_id, loop)"
)
am_content = am_content.replace(
    "self.play_sound(filepath_primary, filepath_secondary, name, volume, primary_device_name, secondary_device_name, dual_enabled, 0.0, sound_id)",
    "self.play_sound(filepath_primary, filepath_secondary, name, volume, primary_device_name, secondary_device_name, dual_enabled, 0.0, sound_id, loop)"
)
am_content = am_content.replace(
    "\"sound_id\": sound_id\n                })",
    "\"sound_id\": sound_id,\n                    \"loop\": loop\n                })"
)
am_content = am_content.replace(
    "sound_id=fi[\"sound_id\"]",
    "sound_id=fi[\"sound_id\"],\n            loop=fi[\"loop\"]"
)
get_focused_old = """            if not fi["device"].running:
                if self.playback_queue:
                    self.play_next()
                    # We just started a new sound, get_focused_progress will pick it up on the next call.
                    # Or we could fetch it recursively right now.
                    return self.get_focused_progress()
                return None"""
get_focused_new = """            if not fi["device"].running:
                if fi.get("loop", False):
                    self.seek_focused(0.0)
                    return self.get_focused_progress()
                if self.playback_queue:
                    self.play_next()
                    return self.get_focused_progress()
                return None"""
am_content = am_content.replace(get_focused_old, get_focused_new)
with open("audio_manager.py", "w", encoding="utf-8") as f:
    f.write(am_content)

# 2. Patch hotkey_manager.py
with open("hotkey_manager.py", "r", encoding="utf-8") as f:
    hk_content = f.read()

hk_content = hk_content.replace(
    "sound_id=sound.get(\"id\")",
    "sound_id=sound.get(\"id\"),\n            loop=sound.get(\"loop\", False)"
)
with open("hotkey_manager.py", "w", encoding="utf-8") as f:
    f.write(hk_content)

# 3. Patch ui/main_window.py
with open("ui/main_window.py", "r", encoding="utf-8") as f:
    mw_content = f.read()

mw_content = mw_content.replace(
    "sound_id=sound.get(\"id\")",
    "sound_id=sound.get(\"id\"),\n            loop=sound.get(\"loop\", False)"
)
with open("ui/main_window.py", "w", encoding="utf-8") as f:
    f.write(mw_content)

# 4. Patch ui/views/sound_edit_dialog.py
with open("ui/views/sound_edit_dialog.py", "r", encoding="utf-8") as f:
    se_content = f.read()

se_content = se_content.replace(
    "dual_enabled=self.config.get(\"dual_output_enabled\", False)",
    "dual_enabled=self.config.get(\"dual_output_enabled\", False),\n            loop=self.cb_loop.isChecked()"
)
with open("ui/views/sound_edit_dialog.py", "w", encoding="utf-8") as f:
    f.write(se_content)

print("Loop and Polyphony Engine fully hooked up!")
