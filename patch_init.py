import os

with open("audio_manager.py", "r", encoding="utf-8") as f:
    content = f.read()

init_old = """    def __init__(self):
        self.devices = miniaudio.Devices()
        self.active_playbacks = []
        self.focused_info = None
        self.fade_in_ms = 0
        self.fade_out_ms = 0
        self.playback_queue = []"""

init_new = """    def __init__(self):
        self.devices = miniaudio.Devices()
        self.active_playbacks = []
        self.focused_info = None
        self.fade_in_ms = 0
        self.fade_out_ms = 0
        self.playback_queue = []
        self.play_mode = "overlay"  # Default mode"""

content = content.replace(init_old, init_new)

with open("audio_manager.py", "w", encoding="utf-8") as f:
    f.write(content)

print("audio_manager.py init fixed")
