import os

with open("audio_manager.py", "r", encoding="utf-8") as f:
    content = f.read()

fi_old = """                self.focused_info = {
                    "sound_id": sound_id,
                    "filepath_primary": filepath_primary,
                    "filepath_secondary": filepath_secondary,
                    "name": name,
                    "duration": info.duration,
                    "start_sys_time": time.time(),
                    "seek_offset": seek_offset,
                    "primary_device_name": primary_device_name,
                    "secondary_device_name": secondary_device_name,
                    "dual_enabled": dual_enabled,
                    "device": dev1,
                    "fade_state": fade_state1,
                }"""

fi_new = """                self.focused_info = {
                    "sound_id": sound_id,
                    "filepath_primary": filepath_primary,
                    "filepath_secondary": filepath_secondary,
                    "name": name,
                    "duration": info.duration,
                    "start_sys_time": time.time(),
                    "seek_offset": seek_offset,
                    "primary_device_name": primary_device_name,
                    "secondary_device_name": secondary_device_name,
                    "dual_enabled": dual_enabled,
                    "device": dev1,
                    "fade_state": fade_state1,
                    "loop": loop,
                    "is_paused": False,
                }"""

content = content.replace(fi_old, fi_new)

with open("audio_manager.py", "w", encoding="utf-8") as f:
    f.write(content)

print("audio_manager.py focused_info fixed")
