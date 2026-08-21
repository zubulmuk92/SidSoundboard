import os

with open("ui/widgets/waveform.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add duration and hover tracking in __init__
init_old = """    def __init__(self, color=None, interactive=False, parent=None):
        super().__init__(parent)
        self.peaks = []
        self.progress = 0.0
        self.base_color = QColor(BG_HOVER)
        self.played_color = QColor(color or ACCENT)
        self.interactive = interactive
        self.setMinimumHeight(28)"""

init_new = """    def __init__(self, color=None, interactive=False, parent=None):
        super().__init__(parent)
        self.peaks = []
        self.progress = 0.0
        self.duration = 0.0
        self.hover_ratio = None
        self.base_color = QColor(BG_HOVER)
        self.played_color = QColor(color or ACCENT)
        self.interactive = interactive
        self.setMinimumHeight(28)
        if self.interactive:
            self.setMouseTracking(True)"""

content = content.replace(init_old, init_new)

# 2. Add mouse tracking methods
mouse_old = """    def mousePressEvent(self, event):
        if self.interactive and self.width() > 0:
            ratio = max(0.0, min(1.0, event.position().x() / self.width()))
            self.seek_requested.emit(ratio)"""

mouse_new = """    def mousePressEvent(self, event):
        if self.interactive and self.width() > 0:
            ratio = max(0.0, min(1.0, event.position().x() / self.width()))
            self.seek_requested.emit(ratio)

    def mouseMoveEvent(self, event):
        if self.interactive and self.width() > 0:
            self.hover_ratio = max(0.0, min(1.0, event.position().x() / self.width()))
            self.update()

    def leaveEvent(self, event):
        if self.interactive:
            self.hover_ratio = None
            self.update()"""

content = content.replace(mouse_old, mouse_new)

# 3. Add text drawing in paintEvent
paint_end_old = """        painter.setPen(Qt.NoPen)
        for i, amplitude in enumerate(self.peaks):
            x = i * bar_width
            bar_h = max(1.0, amplitude * (h - 4))
            painter.setBrush(self.played_color if i < split_index else self.base_color)
            painter.drawRect(int(x), int(mid - bar_h / 2), max(1, int(bar_width) - 1), int(bar_h))

        painter.end()"""

paint_end_new = """        painter.setPen(Qt.NoPen)
        for i, amplitude in enumerate(self.peaks):
            x = i * bar_width
            bar_h = max(1.0, amplitude * (h - 4))
            painter.setBrush(self.played_color if i < split_index else self.base_color)
            painter.drawRect(int(x), int(mid - bar_h / 2), max(1, int(bar_width) - 1), int(bar_h))

        if self.hover_ratio is not None and self.duration > 0:
            hx = self.hover_ratio * w
            # Draw line
            painter.setPen(QPen(QColor("#fff"), 1))
            painter.drawLine(int(hx), 0, int(hx), int(h))
            
            # Draw time text
            time_sec = self.hover_ratio * self.duration
            mins = int(time_sec // 60)
            secs = int(time_sec % 60)
            time_str = f"{mins}:{secs:02d}"
            
            painter.setPen(QColor("#fff"))
            font = painter.font()
            font.setPointSize(8)
            painter.setFont(font)
            fm = painter.fontMetrics()
            tw = fm.horizontalAdvance(time_str)
            tx = hx + 4
            if tx + tw > w:
                tx = hx - tw - 4
            painter.drawText(int(tx), int(h - 4), time_str)

        painter.end()"""

content = content.replace(paint_end_old, paint_end_new)

with open("ui/widgets/waveform.py", "w", encoding="utf-8") as f:
    f.write(content)

print("waveform.py patched")
