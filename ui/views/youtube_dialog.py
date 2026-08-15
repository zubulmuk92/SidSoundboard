"""YouTube import, split out of library_view.py which had grown to do the
grid, both import paths and persistence at once."""

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import (
    QDialog, QLineEdit, QMessageBox, QProgressBar, QPushButton, QVBoxLayout
)

import paths
from i18n import tr
from yt_downloader import download_youtube_audio_async


class _Signals(QObject):
    progress = Signal(int)
    done = Signal(bool, list, str)


class YoutubeDialog(QDialog):
    """Asks for a URL, downloads in the background, and hands the caller
    the list of (filepath, title) pairs it produced."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.results = []
        self.setWindowTitle(tr("yt.title"))
        self.setFixedSize(420, 200)

        layout = QVBoxLayout(self)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText(tr("yt.url"))
        layout.addWidget(self.url_input)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText(tr("yt.name"))
        layout.addWidget(self.title_input)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.btn_download = QPushButton(tr("yt.download"))
        self.btn_download.setProperty("class", "accent")
        self.btn_download.clicked.connect(self._start)
        layout.addWidget(self.btn_download)

        self._signals = _Signals()
        self._signals.progress.connect(self.progress_bar.setValue)
        self._signals.done.connect(self._finish)

    def chosen_name(self):
        return self.title_input.text().strip()

    def _start(self):
        url = self.url_input.text().strip()
        if not url:
            return
        self.btn_download.setEnabled(False)

        def on_progress(percent_text, _current, _total, _speed):
            try:
                self._signals.progress.emit(int(float(percent_text.replace("%", "").strip())))
            except ValueError:
                pass

        def on_done(success, results, error):
            self._signals.done.emit(success, results or [], error)

        download_youtube_audio_async(url, paths.downloads_dir(), on_done, on_progress)

    def _finish(self, success, results, error):
        if success and results:
            self.results = results
            self.accept()
            return

        self.btn_download.setEnabled(True)
        QMessageBox.critical(self, tr("common.error"), tr("yt.failed", error=error))
