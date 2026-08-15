import json
import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from ui.theme import ACCENT, BG_HOVER


def load_peaks(peaks_path):
    if not peaks_path or not os.path.exists(peaks_path):
        return []
    try:
        with open(peaks_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("peaks", [])
    except (OSError, ValueError):
        return []


class WaveformWidget(QWidget):
    seek_requested = Signal(float)

    def __init__(self, color=None, interactive=False, parent=None):
        super().__init__(parent)
        self.peaks = []
        self.progress = 0.0
        self.base_color = QColor(BG_HOVER)
        self.played_color = QColor(color or ACCENT)
        self.interactive = interactive
        self.setMinimumHeight(28)

    def set_peaks(self, peaks):
        peaks = peaks or []
        if peaks != self.peaks:
            self.peaks = peaks
            self.update()

    def set_progress(self, progress):
        progress = max(0.0, min(1.0, progress))
        if progress != self.progress:
            self.progress = progress
            self.update()

    def mousePressEvent(self, event):
        if self.interactive and self.width() > 0:
            ratio = max(0.0, min(1.0, event.position().x() / self.width()))
            self.seek_requested.emit(ratio)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height()
        mid = h / 2

        if not self.peaks:
            painter.setPen(QPen(self.base_color, 1))
            painter.drawLine(0, int(mid), w, int(mid))
            painter.end()
            return

        n = len(self.peaks)
        bar_width = max(1.0, w / n)
        split_index = int(n * self.progress)

        painter.setPen(Qt.NoPen)
        for i, amplitude in enumerate(self.peaks):
            x = i * bar_width
            bar_h = max(1.0, amplitude * (h - 4))
            painter.setBrush(self.played_color if i < split_index else self.base_color)
            painter.drawRect(int(x), int(mid - bar_h / 2), max(1, int(bar_width) - 1), int(bar_h))

        painter.end()
