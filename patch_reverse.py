import os

with open("audio_processor.py", "r", encoding="utf-8") as f:
    content = f.read()

# Add reverse support
reverse_old = """    reverb = _effect(sound, "reverb")
    if reverb > 0:
        delay = int(round(40 + reverb * 1.6))
        decay = round(0.3 + reverb * 0.004, 3)
        filters.append(f"aecho=0.8:0.9:{delay}:{decay}")"""

reverse_new = """    reverb = _effect(sound, "reverb")
    if reverb > 0:
        delay = int(round(40 + reverb * 1.6))
        decay = round(0.3 + reverb * 0.004, 3)
        filters.append(f"aecho=0.8:0.9:{delay}:{decay}")

    if sound.get("reverse", False):
        filters.append("areverse")"""
content = content.replace(reverse_old, reverse_new)

with open("audio_processor.py", "w", encoding="utf-8") as f:
    f.write(content)

with open("config_manager.py", "r", encoding="utf-8") as f:
    c_content = f.read()
c_content = c_content.replace('"loop": False,\n', '"loop": False,\n    "reverse": False,\n')
with open("config_manager.py", "w", encoding="utf-8") as f:
    f.write(c_content)

with open("ui/views/sound_edit_dialog.py", "r", encoding="utf-8") as f:
    se_content = f.read()

# Add Reverse checkbox next to loop
loop_old = """        self.cb_loop = QCheckBox("Jouer en boucle")
        self.cb_loop.setChecked(bool(self.sound.get("loop", False)))
        sliders.addRow(self.cb_loop)"""
loop_new = """        from PySide6.QtWidgets import QHBoxLayout
        cb_layout = QHBoxLayout()
        self.cb_loop = QCheckBox("Jouer en boucle")
        self.cb_loop.setChecked(bool(self.sound.get("loop", False)))
        self.cb_reverse = QCheckBox("Inverser (Reverse)")
        self.cb_reverse.setChecked(bool(self.sound.get("reverse", False)))
        cb_layout.addWidget(self.cb_loop)
        cb_layout.addWidget(self.cb_reverse)
        sliders.addRow(cb_layout)"""
se_content = se_content.replace(loop_old, loop_new)

save_old = """            "loop": self.cb_loop.isChecked(),"""
save_new = """            "loop": self.cb_loop.isChecked(),
            "reverse": self.cb_reverse.isChecked(),"""
se_content = se_content.replace(save_old, save_new)

with open("ui/views/sound_edit_dialog.py", "w", encoding="utf-8") as f:
    f.write(se_content)

print("Reverse feature added")
