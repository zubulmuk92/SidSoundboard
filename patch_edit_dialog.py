import os

with open("ui/views/sound_edit_dialog.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Import QCheckBox
if "QCheckBox" not in content:
    content = content.replace("QComboBox, QDialog, QFormLayout", "QCheckBox, QComboBox, QDialog, QFormLayout")

# 2. Add Loop checkbox to the UI
loop_old = """        self.sl_fade_out = self._slider(
            sliders, tr("editor.fade_out"), 0, 5000,
            self.sound.get("fade_out_ms", self.config.get("fade_out_ms", 150)), " ms",
        )
        layout.addLayout(sliders)"""

loop_new = """        self.sl_fade_out = self._slider(
            sliders, tr("editor.fade_out"), 0, 5000,
            self.sound.get("fade_out_ms", self.config.get("fade_out_ms", 150)), " ms",
        )
        
        self.cb_loop = QCheckBox("Jouer en boucle")
        self.cb_loop.setChecked(bool(self.sound.get("loop", False)))
        sliders.addRow(self.cb_loop)
        
        layout.addLayout(sliders)"""

content = content.replace(loop_old, loop_new)

# 3. Save the Loop state
save_old = """            "fade_in_ms": self.sl_fade_in.value(),
            "fade_out_ms": self.sl_fade_out.value(),
            "trim_start_sec": round(start, 3),
            "trim_end_sec": round(end, 3) if end < self.duration else None,
        }"""

save_new = """            "fade_in_ms": self.sl_fade_in.value(),
            "fade_out_ms": self.sl_fade_out.value(),
            "trim_start_sec": round(start, 3),
            "trim_end_sec": round(end, 3) if end < self.duration else None,
            "loop": self.cb_loop.isChecked(),
        }"""

content = content.replace(save_old, save_new)

with open("ui/views/sound_edit_dialog.py", "w", encoding="utf-8") as f:
    f.write(content)

# 4. Remove fade_in_sec from config_manager.py
with open("config_manager.py", "r", encoding="utf-8") as f:
    config_content = f.read()

config_content = config_content.replace('    "fade_in_sec": 0.0,\n    "fade_out_sec": 0.0,\n', '')

with open("config_manager.py", "w", encoding="utf-8") as f:
    f.write(config_content)

print("sound_edit_dialog.py and config_manager.py patched")
