"""
The performance screen.

The Library is an administration screen — sliders, combos, edit buttons.
Mid-game you want the opposite: large targets and a single possible
action. Nothing here modifies a sound; that constraint is the point of the
screen, not a gap to fill later.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget
)

import profiles
from i18n import tr
from ui.theme import ACCENT, ACCENT_TEXT, BG_PANEL, CATEGORY_COLORS, EDGE, TEXT_MAIN, TEXT_MUTED


class SoundPad(QPushButton):
    """One sound, one target. Shows its name, its key, and its progress."""

    PAD_SIZE = 150

    def __init__(self, sound, parent=None):
        super().__init__(parent)
        self.sound = sound
        self.progress = 0.0
        self._playing = False
        self.setFixedSize(self.PAD_SIZE, self.PAD_SIZE)
        self.setCursor(Qt.PointingHandCursor)

        hotkey = sound.get("hotkey")
        hotkey = "" if not hotkey or hotkey == "None" else hotkey.upper()
        self.setText(f"{sound.get('name', '')}\n\n{hotkey}")
        self._apply_style()

    def _apply_style(self):
        category = CATEGORY_COLORS.get(self.sound.get("color", "Gris"), TEXT_MUTED)
        background = ACCENT if self._playing else BG_PANEL
        color = ACCENT_TEXT if self._playing else TEXT_MAIN
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {background};
                color: {color};
                border: 1px solid {EDGE};
                border-bottom: 4px solid {category};
                border-radius: 10px;
                font-size: 13px;
                font-weight: 600;
                padding: 8px;
                text-align: center;
            }}
            QPushButton:hover {{ border: 1px solid {ACCENT}; border-bottom: 4px solid {category}; }}
        """)

    def set_playing(self, playing, progress=0.0):
        if playing != self._playing:
            self._playing = playing
            self._apply_style()
        if progress != self.progress:
            self.progress = progress
            self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self._playing or self.progress <= 0:
            return

        from PySide6.QtGui import QColor, QPainter
        painter = QPainter(self)
        width = int(self.width() * max(0.0, min(1.0, self.progress)))
        painter.fillRect(0, self.height() - 4, width, 4, QColor(ACCENT_TEXT))
        painter.end()


class SceneView(QWidget):
    sound_triggered = Signal(str)

    PAD_SPACING = 12

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.pads = {}
        self._build()
        self.refresh()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.grid = QGridLayout(self.scroll_widget)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(self.PAD_SPACING)
        self.grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.scroll_area.setWidget(self.scroll_widget)
        layout.addWidget(self.scroll_area)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.refresh()

    def refresh(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.pads = {}

        sounds = profiles.active_sounds(self.config)
        if not sounds:
            label = QLabel(tr("scene.empty"))
            label.setObjectName("EmptyState")
            label.setAlignment(Qt.AlignCenter)
            self.grid.addWidget(label, 0, 0)
            return

        step = SoundPad.PAD_SIZE + self.PAD_SPACING
        width = self.scroll_area.viewport().width()
        columns = max(1, (width + self.PAD_SPACING) // step)

        for index, sound in enumerate(sounds):
            row, column = divmod(index, columns)
            pad = SoundPad(sound)
            pad.clicked.connect(lambda _=False, s=sound: self.sound_triggered.emit(s["id"]))
            self.pads[sound["id"]] = pad
            self.grid.addWidget(pad, row, column)

    def set_playing(self, sound_id, progress):
        """Marks one pad as playing and clears every other one."""
        for pad_id, pad in self.pads.items():
            pad.set_playing(pad_id == sound_id, progress if pad_id == sound_id else 0.0)
