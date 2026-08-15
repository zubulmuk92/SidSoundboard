from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter

from ui.theme import ACCENT, BG_APP
from ui.widgets.waveform import WaveformWidget


class TrimWaveformWidget(WaveformWidget):
    """
    Waveform with two draggable handles delimiting the kept region. The
    peaks shown are those of the original file, so the user keeps the full
    context of the sound while choosing where to cut.
    """

    trim_changed = Signal(float, float)

    GRAB_PX = 10

    def __init__(self, parent=None):
        super().__init__(interactive=False, parent=parent)
        self.start_ratio = 0.0
        self.end_ratio = 1.0
        self._dragging = None
        self.setMinimumHeight(90)
        self.setCursor(Qt.SizeHorCursor)

    def set_trim(self, start_ratio, end_ratio):
        self.start_ratio = max(0.0, min(1.0, start_ratio))
        self.end_ratio = max(self.start_ratio, min(1.0, end_ratio))
        self.update()

    def _ratio_at(self, x):
        if self.width() <= 0:
            return 0.0
        return max(0.0, min(1.0, x / self.width()))

    def mousePressEvent(self, event):
        x = event.position().x()
        start_x = self.start_ratio * self.width()
        end_x = self.end_ratio * self.width()
        if abs(x - start_x) <= self.GRAB_PX:
            self._dragging = "start"
        elif abs(x - end_x) <= self.GRAB_PX:
            self._dragging = "end"
        else:
            # Clicking away from both handles grabs the nearer one, so a
            # coarse click still does something useful.
            self._dragging = "start" if abs(x - start_x) < abs(x - end_x) else "end"
        self._drag_to(x)

    def mouseMoveEvent(self, event):
        if self._dragging:
            self._drag_to(event.position().x())

    def mouseReleaseEvent(self, event):
        self._dragging = None

    def _drag_to(self, x):
        ratio = self._ratio_at(x)
        if self._dragging == "start":
            self.start_ratio = min(ratio, self.end_ratio)
        else:
            self.end_ratio = max(ratio, self.start_ratio)
        self.update()
        self.trim_changed.emit(self.start_ratio, self.end_ratio)

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        w = self.width()
        h = self.height()
        start_x = int(self.start_ratio * w)
        end_x = int(self.end_ratio * w)

        # Dim what will be cut away.
        dim = QColor(BG_APP)
        dim.setAlpha(190)
        painter.fillRect(0, 0, start_x, h, dim)
        painter.fillRect(end_x, 0, w - end_x, h, dim)

        handle = QColor(ACCENT)
        painter.fillRect(max(0, start_x - 1), 0, 3, h, handle)
        painter.fillRect(min(w - 3, end_x - 1), 0, 3, h, handle)
        painter.end()
