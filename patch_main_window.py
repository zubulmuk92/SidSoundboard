import os

with open("ui/main_window.py", "r", encoding="utf-8") as f:
    content = f.read()

connect_old = """        self.player_bar.seek_requested.connect(self._on_seek)
        self.player_bar.skip_requested.connect(self._on_skip)"""
connect_new = """        self.player_bar.seek_requested.connect(self._on_seek)
        self.player_bar.skip_requested.connect(self._on_skip)
        self.player_bar.mode_changed.connect(self._on_play_mode_changed)"""

content = content.replace(connect_old, connect_new)

method_old = """    @Slot()
    def _on_skip(self):
        self.audio_manager.play_next()"""
method_new = """    @Slot()
    def _on_skip(self):
        self.audio_manager.play_next()

    @Slot(str)
    def _on_play_mode_changed(self, mode):
        self.audio_manager.play_mode = mode"""

content = content.replace(method_old, method_new)

with open("ui/main_window.py", "w", encoding="utf-8") as f:
    f.write(content)

print("main_window.py patched")
