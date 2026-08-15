from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout

from ui.theme import BG_APP, CATEGORY_COLORS, TEXT_MAIN, TEXT_MUTED, get_icon
from ui.widgets.waveform import WaveformWidget, load_peaks


class SoundCard(QFrame):
    play_requested = Signal(str)
    delete_requested = Signal(str)
    hotkey_requested = Signal(str, object)
    volume_changed = Signal(str, int)
    color_changed = Signal(str, str)

    def __init__(self, sound, parent=None):
        super().__init__(parent)
        self.sound = sound
        self.setObjectName("SoundCard")
        self.setFixedSize(300, 130)
        self._build()

    def _build(self):
        cat = self.sound.get("color", "Gris")
        cat_hex = CATEGORY_COLORS.get(cat, "#8B8D93")
        if cat != "Gris":
            self.setStyleSheet(f"#SoundCard {{ border-left: 4px solid {cat_hex}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)

        top_row = QHBoxLayout()
        name_lbl = QLabel(self.sound.get("name", "Unknown"))
        name_lbl.setStyleSheet(f"font-weight: 600; font-size: 14px; color: {TEXT_MAIN};")
        top_row.addWidget(name_lbl)
        top_row.addStretch()

        self.hk_btn = QPushButton(self.sound.get("hotkey", "None"))
        self.hk_btn.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; background: {BG_APP}; padding: 2px 6px; border-radius: 4px;")
        self.hk_btn.clicked.connect(lambda: self.hotkey_requested.emit(self.sound["id"], self.hk_btn))
        top_row.addWidget(self.hk_btn)

        btn_del = QPushButton()
        btn_del.setIcon(get_icon("delete.svg"))
        btn_del.setProperty("class", "danger")
        btn_del.setFixedSize(28, 28)
        btn_del.clicked.connect(lambda: self.delete_requested.emit(self.sound["id"]))
        top_row.addWidget(btn_del)

        layout.addLayout(top_row)

        self.waveform = WaveformWidget(interactive=False)
        peaks_path = (self.sound.get("filename") or "") + ".peaks.json"
        self.waveform.set_peaks(load_peaks(peaks_path))
        layout.addWidget(self.waveform)

        bot_row = QHBoxLayout()
        btn_play = QPushButton(" PLAY")
        btn_play.setIcon(get_icon("play.svg"))
        btn_play.setProperty("class", "accent")
        btn_play.setFixedSize(85, 26)
        btn_play.clicked.connect(lambda: self.play_requested.emit(self.sound["id"]))
        bot_row.addWidget(btn_play)

        vol_slider = QSlider(Qt.Horizontal)
        vol_slider.setRange(0, 400)
        vol_slider.setValue(self.sound.get("volume", 100))
        vol_slider.setFixedWidth(80)
        vol_slider.sliderReleased.connect(lambda: self.volume_changed.emit(self.sound["id"], vol_slider.value()))
        bot_row.addWidget(vol_slider)

        cb_color = QComboBox()
        cb_color.addItems(list(CATEGORY_COLORS.keys()))
        cb_color.setCurrentText(cat)
        cb_color.setFixedWidth(80)
        cb_color.currentTextChanged.connect(lambda c: self.color_changed.emit(self.sound["id"], c))
        bot_row.addWidget(cb_color)

        layout.addLayout(bot_row)

    def set_playback_progress(self, ratio):
        self.waveform.set_progress(ratio)
