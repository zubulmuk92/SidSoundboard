import os

with open("audio_manager.py", "r", encoding="utf-8") as f:
    content = f.read()

seek_old = """    def seek_focused(self, time_seconds):
        if not self.focused_info:
            return
            
        # Sauvegarder la référence AVANT de faire stop_all
        fi = self.focused_info
        
        # Stop everything playing right now to restart from seek position
        self.stop_all()
        
        # Re-play with new offset
        self.play_sound(
            filepath_primary=fi["filepath_primary"],
            filepath_secondary=fi["filepath_secondary"],
            name=fi["name"],
            primary_device_name=fi["primary_device_name"],
            secondary_device_name=fi["secondary_device_name"],
            dual_enabled=fi["dual_enabled"],
            seek_offset=time_seconds,
            sound_id=fi["sound_id"],
            loop=fi["loop"]
        )"""

seek_new = """    def seek_focused(self, time_seconds):
        if not self.focused_info:
            return
            
        fi = self.focused_info
        
        # Stop ONLY the currently focused sound, not everything!
        # Find the playbacks for this sound_id and close them
        remaining = []
        for entry in self.active_playbacks:
            # entry: (device, stream, fade_state, sound_id)
            if entry[3] == fi.get("sound_id") and entry[0] == fi.get("device"):
                self._close_entry(entry)
            else:
                remaining.append(entry)
        self.active_playbacks = remaining
        
        # Re-play with new offset
        self.play_sound(
            filepath_primary=fi["filepath_primary"],
            filepath_secondary=fi["filepath_secondary"],
            name=fi["name"],
            primary_device_name=fi["primary_device_name"],
            secondary_device_name=fi["secondary_device_name"],
            dual_enabled=fi["dual_enabled"],
            seek_offset=time_seconds,
            sound_id=fi["sound_id"],
            loop=fi.get("loop", False)
        )"""

content = content.replace(seek_old, seek_new)

with open("audio_manager.py", "w", encoding="utf-8") as f:
    f.write(content)

print("audio_manager.py seek fixed")
