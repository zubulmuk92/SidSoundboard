import os

with open("audio_manager.py", "r", encoding="utf-8") as f:
    content = f.read()

play_next_old = """    def play_next(self):
        if not self.playback_queue:
            self.stop_all()
            return False
        
        next_sound = self.playback_queue.pop(0)
        self.stop_all()
        self.play_sound(**next_sound)
        return True"""

play_next_new = """    def play_next(self):
        if self.play_mode == "overlay":
            # Just stop the focused sound
            if self.focused_info:
                self.stop_sound(self.focused_info.get("sound_id"))
            return True
            
        if not self.playback_queue:
            self.stop_all()
            return False
        
        next_sound = self.playback_queue.pop(0)
        self.stop_all()
        self.play_sound(**next_sound)
        return True"""

content = content.replace(play_next_old, play_next_new)

with open("audio_manager.py", "w", encoding="utf-8") as f:
    f.write(content)

print("audio_manager.py play_next fixed")
