import os
import threading

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QSlider, QVBoxLayout, QWidget
)

from audio_processor import generate_effects_cache
from i18n import category_key, category_label, tr
from ui.theme import CATEGORY_COLORS, TEXT_MAIN, TEXT_MUTED
from ui.widgets.trim_waveform import TrimWaveformWidget
from ui.widgets.waveform import load_peaks


def sound_duration(filepath):
    """Duration in seconds, 0.0 if the file cannot be probed."""
    try:
        import miniaudio
        return miniaudio.get_file_info(filepath).duration
    except Exception:
        return 0.0


class SoundEditDialog(QDialog):
    """Per-sound editor: rename, categorize, trim, and apply effects."""

    render_done = Signal(bool, str, str)

    def __init__(self, sound, config, audio_manager, parent=None):
        super().__init__(parent)
        self.sound = sound
        self.config = config
        self.audio_manager = audio_manager
        self.duration = sound_duration(sound.get("filename") or "")
        self._pending_save = False

        self.setWindowTitle(tr("editor.title", name=sound.get("name", "")))
        self.setMinimumWidth(560)
        self.render_done.connect(self._on_render_done)
        self._build()

    # ---------- construction ----------

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header = QFormLayout()
        self.name_input = QLineEdit(self.sound.get("name", ""))
        header.addRow(tr("editor.name"), self.name_input)

        self.cb_color = QComboBox()
        self.cb_color.addItems([category_label(k) for k in CATEGORY_COLORS])
        self.cb_color.setCurrentText(category_label(self.sound.get("color", "Gris")))
        header.addRow(tr("editor.category"), self.cb_color)
        layout.addLayout(header)

        cut_lbl = QLabel(tr("editor.trim_hint"))
        cut_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        layout.addWidget(cut_lbl)

        self.trim_widget = TrimWaveformWidget()
        self.trim_widget.set_peaks(load_peaks((self.sound.get("filename") or "") + ".peaks.json"))
        start = float(self.sound.get("trim_start_sec") or 0.0)
        end = self.sound.get("trim_end_sec")
        end = float(end) if end else self.duration
        if self.duration > 0:
            self.trim_widget.set_trim(start / self.duration, min(1.0, end / self.duration))
        self.trim_widget.trim_changed.connect(self._on_trim_changed)
        layout.addWidget(self.trim_widget)

        self.lbl_trim = QLabel()
        self.lbl_trim.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        self.lbl_trim.setAlignment(Qt.AlignRight)
        layout.addWidget(self.lbl_trim)
        self._on_trim_changed(self.trim_widget.start_ratio, self.trim_widget.end_ratio)

        sliders = QFormLayout()
        sliders.setSpacing(10)
        self.sl_volume = self._slider(sliders, tr("editor.volume"), 0, 400, self.sound.get("volume", 100), "%")
        self.sl_speed = self._slider(
            sliders, tr("editor.speed"), 50, 200, self.sound.get("speed", 100), "%",
            hint=tr("editor.speed_hint"),
        )
        self.sl_bass = self._slider(sliders, tr("editor.bass"), 0, 100, self.sound.get("bass_boost", 0), "%")
        self.sl_reverb = self._slider(sliders, tr("editor.reverb"), 0, 100, self.sound.get("reverb", 0), "%")
        self.sl_fade_in = self._slider(
            sliders, tr("editor.fade_in"), 0, 5000,
            self.sound.get("fade_in_ms", self.config.get("fade_in_ms", 150)), " ms",
        )
        self.sl_fade_out = self._slider(
            sliders, tr("editor.fade_out"), 0, 5000,
            self.sound.get("fade_out_ms", self.config.get("fade_out_ms", 150)), " ms",
        )
        
        from PySide6.QtWidgets import QHBoxLayout
        cb_layout = QHBoxLayout()
        self.cb_loop = QCheckBox("Jouer en boucle")
        self.cb_loop.setChecked(bool(self.sound.get("loop", False)))
        self.cb_reverse = QCheckBox("Inverser (Reverse)")
        self.cb_reverse.setChecked(bool(self.sound.get("reverse", False)))
        cb_layout.addWidget(self.cb_loop)
        cb_layout.addWidget(self.cb_reverse)
        sliders.addRow(cb_layout)
        
        layout.addLayout(sliders)

        buttons = QHBoxLayout()
        self.btn_preview = QPushButton(tr("editor.preview"))
        self.btn_preview.clicked.connect(self._preview)
        buttons.addWidget(self.btn_preview)
        buttons.addStretch()

        btn_cancel = QPushButton(tr("common.cancel"))
        btn_cancel.clicked.connect(self.reject)
        buttons.addWidget(btn_cancel)

        self.btn_save = QPushButton(tr("editor.save"))
        self.btn_save.setProperty("class", "accent")
        self.btn_save.clicked.connect(self._save)
        buttons.addWidget(self.btn_save)
        layout.addLayout(buttons)

    def _slider(self, form, label, minimum, maximum, value, suffix, hint=None):
        slider = QSlider(Qt.Horizontal)
        slider.setRange(minimum, maximum)
        slider.setValue(int(value if value is not None else minimum))

        value_lbl = QLabel(f"{slider.value()}{suffix}")
        value_lbl.setFixedWidth(60)
        value_lbl.setStyleSheet(f"color: {TEXT_MAIN}; font-size: 11px;")
        slider.valueChanged.connect(lambda v: value_lbl.setText(f"{v}{suffix}"))

        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.addWidget(slider)
        row_layout.addWidget(value_lbl)

        if hint:
            hint_lbl = QLabel(hint)
            hint_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px;")
            row_layout.addWidget(hint_lbl)

        form.addRow(label, row)
        return slider

    # ---------- values ----------

    def _on_trim_changed(self, start_ratio, end_ratio):
        start = start_ratio * self.duration
        end = end_ratio * self.duration
        self.lbl_trim.setText(tr("editor.trim_range", start=start, end=end, length=end - start))

    def _current_values(self):
        start = self.trim_widget.start_ratio * self.duration
        end = self.trim_widget.end_ratio * self.duration
        return {
            "name": self.name_input.text().strip() or self.sound.get("name", "Son"),
            "color": category_key(self.cb_color.currentText()),
            "volume": self.sl_volume.value(),
            "speed": self.sl_speed.value(),
            "bass_boost": self.sl_bass.value(),
            "reverb": self.sl_reverb.value(),
            "fade_in_ms": self.sl_fade_in.value(),
            "fade_out_ms": self.sl_fade_out.value(),
            "trim_start_sec": round(start, 3),
            "trim_end_sec": round(end, 3) if end < self.duration else None,
            "loop": self.cb_loop.isChecked(),
            "reverse": self.cb_reverse.isChecked(),
        }

    # ---------- rendering ----------

    def _render_async(self, suffix, with_peaks, pending_save):
        self._pending_save = pending_save
        self.btn_preview.setEnabled(False)
        self.btn_save.setEnabled(False)
        self.btn_preview.setText(tr("editor.rendering"))

        # Any render overwrites a file this dialog may currently be
        # playing (the sound itself, or an earlier preview). FFmpeg cannot
        # overwrite a file miniaudio still holds open.
        self.audio_manager.stop_all()

        draft = dict(self.sound)
        draft.update(self._current_values())

        def worker():
            try:
                path = generate_effects_cache(
                    draft, os.path.dirname(os.path.abspath(draft["filename"])),
                    suffix=suffix, with_peaks=with_peaks,
                )
                self.render_done.emit(True, path, "")
            except Exception as e:
                self.render_done.emit(False, "", str(e))

        threading.Thread(target=worker, daemon=True).start()

    def _on_render_done(self, success, path, error):
        self.btn_preview.setEnabled(True)
        self.btn_save.setEnabled(True)
        self.btn_preview.setText(tr("editor.preview"))

        if not success:
            QMessageBox.critical(self, tr("common.error"), tr("editor.render_failed", error=error))
            return

        if self._pending_save:
            self.sound.update(self._current_values())
            self.sound["cached_effects_file"] = path
            self.accept()
        else:
            self._play_preview(path)

    def _preview(self):
        self._render_async("_preview", with_peaks=False, pending_save=False)

    def _play_preview(self, path):
        self.audio_manager.stop_all()
        self.audio_manager.set_fade_durations(self.sl_fade_in.value(), self.sl_fade_out.value())
        self.audio_manager.play_sound(
            filepath_primary=path,
            filepath_secondary=None,
            name=self.name_input.text(),
            primary_device_name=self.config.get("primary_output"),
            dual_enabled=False,
            sound_id=None,
        )

    def _save(self):
        self._render_async("_fx", with_peaks=True, pending_save=True)

    def reject(self):
        self.audio_manager.stop_all()
        super().reject()
