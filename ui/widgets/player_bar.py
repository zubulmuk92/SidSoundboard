from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton

from i18n import tr
from ui.widgets.waveform import WaveformWidget


class PlayerBar(QFrame):
    seek_requested = Signal(float)
    skip_requested = Signal()
    mode_changed = Signal(str)

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

        self.lbl_queue = QLabel("")
        self.lbl_queue.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.lbl_queue)

        from PySide6.QtWidgets import QPushButton
        
        self.btn_mode = QPushButton("🔉 Superposition")
        self.btn_mode.setToolTip("Changer le mode de lecture (Superposition ou File d'attente)")
        self.btn_mode.setCheckable(True)
        self.btn_mode.clicked.connect(self._toggle_mode)
        layout.addWidget(self.btn_mode)

        self.btn_skip = QPushButton("Passer")
        self.btn_skip.clicked.connect(self.skip_requested)
        self.btn_skip.hide()
        layout.addWidget(self.btn_skip)

    def _toggle_mode(self, checked):
        if checked:
            self.btn_mode.setText("🔁 File d'attente")
            self.mode_changed.emit("queue")
        else:
            self.btn_mode.setText("🔉 Superposition")
            self.mode_changed.emit("overlay")

    def update_progress(self, name, current, duration, peaks, is_paused=False, queue_count=0):
        if not name:
            self.lbl_playing.setText(tr("player.idle"))
            self.btn_skip.hide()
            self.lbl_queue.setText("")
        else:
            self.lbl_playing.setText(
                tr("player.paused" if is_paused else "player.playing", name=name)
            )
            self.btn_skip.show()
            if queue_count > 0:
                self.lbl_queue.setText(f"+ {queue_count} en attente")
            else:
                self.lbl_queue.setText("")

        self.lbl_time_cur.setText(self._format_time(current))
        self.lbl_time_tot.setText(self._format_time(duration))
        if peaks is not None:
            self.waveform.set_peaks(peaks)
        self.waveform.duration = duration
        self.waveform.set_progress(current / duration if duration > 0 else 0.0)

    @staticmethod
    def _format_time(seconds):
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}:{secs:02d}"
