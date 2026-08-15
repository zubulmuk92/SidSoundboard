"""
First-run guidance.

The virtual cable is the hardest step of the install and the one that
makes the product's whole point work — routing sound into Discord — yet
the app said nothing about it. The README explains it, but nobody reads
the README of an .exe.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

import profiles
from i18n import tr
from ui.theme import ACCENT, DANGER, TEXT_MAIN, TEXT_MUTED

# Substrings found in the device names virtual cables register under.
CABLE_MARKERS = ("vb-audio", "cable", "voicemeeter", "virtual audio")


def find_virtual_cable(device_names):
    """Returns the first device that looks like a virtual cable, or None."""
    for name in device_names:
        lowered = (name or "").lower()
        if any(marker in lowered for marker in CABLE_MARKERS):
            return name
    return None


class WelcomeView(QWidget):
    open_settings = Signal()
    open_library = Signal()

    def __init__(self, audio_manager, config, parent=None):
        super().__init__(parent)
        self.audio_manager = audio_manager
        self.config = config
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        title = QLabel(tr("welcome.title"))
        title.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {TEXT_MAIN};")
        layout.addWidget(title)

        intro = QLabel(tr("welcome.intro"))
        intro.setStyleSheet(f"color: {TEXT_MUTED};")
        layout.addWidget(intro)

        self.steps_layout = QVBoxLayout()
        self.steps_layout.setSpacing(10)
        layout.addLayout(self.steps_layout)
        layout.addStretch()

        self.refresh()

    def _step(self, ok, headline, help_text, button_label=None, on_click=None):
        frame = QFrame()
        frame.setObjectName("SoundCard")
        row = QVBoxLayout(frame)
        row.setContentsMargins(16, 12, 16, 12)

        head = QHBoxLayout()
        bullet = QLabel("●")
        bullet.setStyleSheet(f"color: {ACCENT if ok else DANGER}; font-size: 15px;")
        head.addWidget(bullet)
        label = QLabel(headline)
        label.setStyleSheet(f"font-weight: 600; color: {TEXT_MAIN};")
        head.addWidget(label)
        head.addStretch()

        if button_label and on_click:
            button = QPushButton(button_label)
            button.clicked.connect(on_click)
            head.addWidget(button)
        row.addLayout(head)

        if help_text:
            hint = QLabel(help_text)
            hint.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
            hint.setWordWrap(True)
            hint.setTextInteractionFlags(Qt.TextBrowserInteraction)
            hint.setOpenExternalLinks(True)
            row.addWidget(hint)

        return frame

    def refresh(self):
        while self.steps_layout.count():
            item = self.steps_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        try:
            names = [d["name"] for d in self.audio_manager.get_output_devices()]
        except Exception:
            names = []
        cable = find_virtual_cable(names)

        link = tr("welcome.cable_link")
        self.steps_layout.addWidget(self._step(
            bool(cable),
            tr("welcome.cable_ok", name=cable) if cable else tr("welcome.cable_missing"),
            "" if cable else f'{tr("welcome.cable_help")} <a href="{link}">{link}</a>',
        ))

        dual = self.config.get("dual_output_enabled", False)
        self.steps_layout.addWidget(self._step(
            dual,
            tr("welcome.dual_ok") if dual else tr("welcome.dual_off"),
            "" if dual else tr("welcome.dual_help"),
            None if dual else tr("welcome.open_settings"),
            None if dual else self.open_settings.emit,
        ))

        count = len(profiles.active_sounds(self.config))
        self.steps_layout.addWidget(self._step(
            count > 0,
            tr("welcome.library_ok", count=count) if count else tr("welcome.library_empty"),
            "" if count else tr("welcome.library_help"),
            None if count else tr("welcome.open_library"),
            None if count else self.open_library.emit,
        ))
