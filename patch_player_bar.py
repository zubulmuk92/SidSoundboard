import os

with open("ui/widgets/player_bar.py", "r", encoding="utf-8") as f:
    content = f.read()

btn_skip_old = """        from PySide6.QtWidgets import QPushButton
        self.btn_skip = QPushButton("Passer")
        self.btn_skip.clicked.connect(self.skip_requested)
        self.btn_skip.hide()
        layout.addWidget(self.btn_skip)"""

btn_skip_new = """        from PySide6.QtWidgets import QPushButton
        
        self.btn_mode = QPushButton("🔉 Superposition")
        self.btn_mode.setToolTip("Changer le mode de lecture (Superposition ou File d'attente)")
        self.btn_mode.setCheckable(True)
        self.btn_mode.clicked.connect(self._toggle_mode)
        layout.addWidget(self.btn_mode)

        self.btn_skip = QPushButton("Passer")
        self.btn_skip.clicked.connect(self.skip_requested)
        self.btn_skip.hide()
        layout.addWidget(self.btn_skip)"""
content = content.replace(btn_skip_old, btn_skip_new)

# Add method and mode_changed signal
imports_old = """from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel"""
imports_new = """from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton"""
content = content.replace(imports_old, imports_new)

signal_old = """class PlayerBar(QFrame):
    seek_requested = Signal(float)
    skip_requested = Signal()"""
signal_new = """class PlayerBar(QFrame):
    seek_requested = Signal(float)
    skip_requested = Signal()
    mode_changed = Signal(str)"""
content = content.replace(signal_old, signal_new)

method_old = """    def update_progress(self, name, current, duration, peaks, is_paused=False, queue_count=0):"""
method_new = """    def _toggle_mode(self, checked):
        if checked:
            self.btn_mode.setText("🔁 File d'attente")
            self.mode_changed.emit("queue")
        else:
            self.btn_mode.setText("🔉 Superposition")
            self.mode_changed.emit("overlay")

    def update_progress(self, name, current, duration, peaks, is_paused=False, queue_count=0):"""
content = content.replace(method_old, method_new)

with open("ui/widgets/player_bar.py", "w", encoding="utf-8") as f:
    f.write(content)

print("player_bar.py updated")
