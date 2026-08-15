from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel

from i18n import tr
from ui.widgets.waveform import WaveformWidget


class PlayerBar(QFrame):
    seek_requested = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PlayerBar")
        self.setFixedHeight(60)
        layout = QHBoxLayout(self)

        self.lbl_playing = QLabel(tr("player.idle"))
        self.lbl_playing.setFixedWidth(250)
        layout.addWidget(self.lbl_playing)

        self.lbl_time_cur = QLabel("0:00")
        self.lbl_time_cur.setFixedWidth(40)
        layout.addWidget(self.lbl_time_cur)

        self.waveform = WaveformWidget(interactive=True)
        self.waveform.seek_requested.connect(self.seek_requested)
        layout.addWidget(self.waveform)

        self.lbl_time_tot = QLabel("0:00")
        self.lbl_time_tot.setFixedWidth(40)
        layout.addWidget(self.lbl_time_tot)

    def update_progress(self, name, current, duration, peaks, is_paused=False):
        if not name:
            self.lbl_playing.setText(tr("player.idle"))
        else:
            self.lbl_playing.setText(
                tr("player.paused" if is_paused else "player.playing", name=name)
            )
        self.lbl_time_cur.setText(self._format_time(current))
        self.lbl_time_tot.setText(self._format_time(duration))
        if peaks is not None:
            self.waveform.set_peaks(peaks)
        self.waveform.set_progress(current / duration if duration > 0 else 0.0)

    @staticmethod
    def _format_time(seconds):
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}:{secs:02d}"
