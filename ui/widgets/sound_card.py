from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout

from audio_processor import resolve_playback_file
from i18n import category_key, category_label, tr
from ui.theme import ACCENT_TEXT, BG_APP, CATEGORY_COLORS, TEXT_MAIN, TEXT_MUTED, get_icon
from ui.widgets.waveform import WaveformWidget, load_peaks


class SoundCard(QFrame):
    # Wide enough for the category combo to show a full label without
    # truncating it; the grid derives its column count from this.
    WIDTH = 360
    HEIGHT = 130

    play_requested = Signal(str)
    edit_requested = Signal(str)
    delete_requested = Signal(str)
    hotkey_requested = Signal(str, object)
    volume_changed = Signal(str, int)
    color_changed = Signal(str, str)

    def __init__(self, sound, parent=None):
        super().__init__(parent)
        self.sound = sound
        self.setObjectName("SoundCard")
        self.setFixedSize(self.WIDTH, self.HEIGHT)
        self._playing_state = None
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

        btn_edit = QPushButton()
        btn_edit.setIcon(get_icon("edit.svg"))
        btn_edit.setToolTip(tr("card.edit_tooltip"))
        btn_edit.setFixedSize(28, 28)
        btn_edit.clicked.connect(lambda: self.edit_requested.emit(self.sound["id"]))
        top_row.addWidget(btn_edit)

        btn_del = QPushButton()
        btn_del.setIcon(get_icon("delete.svg"))
        btn_del.setToolTip(tr("card.delete_tooltip"))
        btn_del.setProperty("class", "danger")
        btn_del.setFixedSize(28, 28)
        btn_del.clicked.connect(lambda: self.delete_requested.emit(self.sound["id"]))
        top_row.addWidget(btn_del)

        layout.addLayout(top_row)

        self.waveform = WaveformWidget(interactive=False)
        # Draw the sound as it will actually be heard: the effects render,
        # not the untouched original.
        peaks_path = (resolve_playback_file(self.sound) or "") + ".peaks.json"
        self.waveform.set_peaks(load_peaks(peaks_path))
        layout.addWidget(self.waveform)

        bot_row = QHBoxLayout()
        bot_row.setSpacing(6)
        self.btn_play = QPushButton()
        self.btn_play.setProperty("class", "accent")
        self.btn_play.setFixedSize(78, 26)
        self.btn_play.clicked.connect(lambda: self.play_requested.emit(self.sound["id"]))
        self.set_playing_state("idle")
        bot_row.addWidget(self.btn_play)

        vol_slider = QSlider(Qt.Horizontal)
        vol_slider.setRange(0, 400)
        vol_slider.setValue(self.sound.get("volume", 100))
        vol_slider.setFixedWidth(65)
        bot_row.addWidget(vol_slider)

        vol_label = QLabel(f"{vol_slider.value()}%")
        vol_label.setFixedWidth(34)
        vol_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        vol_slider.valueChanged.connect(lambda v: vol_label.setText(f"{v}%"))
        vol_slider.sliderReleased.connect(lambda: self.volume_changed.emit(self.sound["id"], vol_slider.value()))
        bot_row.addWidget(vol_label)

        cb_color = QComboBox()
        cb_color.addItems([category_label(k) for k in CATEGORY_COLORS])
        cb_color.setCurrentText(category_label(cat))
        cb_color.setFixedWidth(118)
        # The combo shows a localized label; the config keeps the canonical key.
        cb_color.currentTextChanged.connect(
            lambda c: self.color_changed.emit(self.sound["id"], category_key(c))
        )
        bot_row.addWidget(cb_color)

        layout.addLayout(bot_row)

    def set_playback_progress(self, ratio):
        self.waveform.set_progress(ratio)

    def set_playing_state(self, state):
        """
        The button always names what pressing it does next: PAUSE while the
        sound runs, PLAY otherwise. A paused sound reads as PLAY because
        that is what resumes it — the waveform keeps the held position.
        """
        if state == self._playing_state:
            return
        self._playing_state = state

        playing = state == "playing"
        self.btn_play.setText(tr("card.pause" if playing else "card.play"))
        self.btn_play.setIcon(
            get_icon("pause.svg" if playing else "play.svg", ACCENT_TEXT)
        )
