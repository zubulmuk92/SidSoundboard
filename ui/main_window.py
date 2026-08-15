import threading

import keyboard
from PySide6.QtCore import QSize, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton, QStackedWidget,
    QVBoxLayout, QWidget
)

import config_manager
from audio_processor import ensure_caches, resolve_playback_file, resolve_secondary_file
from ui.theme import QSS, TEXT_MAIN, get_icon, resource_path
from ui.views.library_view import LibraryView
from ui.views.settings_view import SettingsView
from ui.widgets.player_bar import PlayerBar
from ui.widgets.waveform import load_peaks


class AppGUI(QMainWindow):
    caches_ready = Signal(int)

    def __init__(self, audio_manager, hotkey_manager, config):
        super().__init__()
        self._cache_rebuild_running = False
        self.caches_ready.connect(self._on_caches_ready)
        self.audio_manager = audio_manager
        self.hotkey_manager = hotkey_manager
        self.config = config
        self._last_timeline_sound_id = None
        self.audio_manager.set_fade_durations(
            self.config.get("fade_in_ms", 150), self.config.get("fade_out_ms", 150)
        )

        self.setWindowTitle("SidSoundboard - Studio Edition")
        self.setWindowIcon(QIcon(resource_path("logo.ico")))
        self.resize(1050, 750)
        self.setMinimumSize(950, 650)
        self.setStyleSheet(QSS)

        self.timeline_timer = QTimer()
        self.timeline_timer.timeout.connect(self._update_timeline)
        self.timeline_timer.start(100)

        self._build_ui()

    def _build_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(220)
        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setContentsMargins(0, 20, 0, 20)

        title = QLabel("SidSoundboard")
        title.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {TEXT_MAIN}; padding-left: 20px;")
        side_layout.addWidget(title)
        side_layout.addSpacing(30)

        self.btn_lib = QPushButton(" Bibliothèque")
        self.btn_lib.setIcon(get_icon("lib.svg"))
        self.btn_lib.setCheckable(True)
        self.btn_lib.setChecked(True)
        self.btn_lib.clicked.connect(lambda: self._switch_tab(0))

        self.btn_set = QPushButton(" Réglages")
        self.btn_set.setIcon(get_icon("settings.svg"))
        self.btn_set.setCheckable(True)
        self.btn_set.clicked.connect(lambda: self._switch_tab(1))

        side_layout.addWidget(self.btn_lib)
        side_layout.addWidget(self.btn_set)
        side_layout.addStretch()

        btn_stop = QPushButton("  ARRÊT D'URGENCE")
        btn_stop.setObjectName("PanicButton")
        btn_stop.setIcon(get_icon("stop.svg", "#FFFFFF"))
        btn_stop.setIconSize(QSize(18, 18))
        btn_stop.setFixedHeight(54)
        btn_stop.setCursor(Qt.PointingHandCursor)
        btn_stop.setToolTip("Coupe immédiatement tous les sons en cours")
        btn_stop.clicked.connect(self._panic_stop)
        side_layout.addWidget(btn_stop)

        self.lbl_panic_hint = QLabel()
        self.lbl_panic_hint.setObjectName("PanicHint")
        self.lbl_panic_hint.setAlignment(Qt.AlignCenter)
        self._refresh_panic_hint()
        side_layout.addWidget(self.lbl_panic_hint)

        main_layout.addWidget(self.sidebar)

        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.addWidget(content_area)

        self.stacked_widget = QStackedWidget()
        content_layout.addWidget(self.stacked_widget)

        self.library_view = LibraryView(self.config, self.audio_manager)
        self.library_view.sound_played.connect(self._play_sound)
        self.library_view.hotkey_bind_requested.connect(self._bind_hotkey)
        self.library_view.sounds_changed.connect(self._on_sounds_changed)
        self.stacked_widget.addWidget(self.library_view)

        self.settings_view = SettingsView(
            self.audio_manager, self.config, self._on_settings_saved, self._bind_panic_key
        )
        self.stacked_widget.addWidget(self.settings_view)

        self.player_bar = PlayerBar()
        self.player_bar.seek_requested.connect(self._on_seek)
        content_layout.addWidget(self.player_bar)

        self._rebuild_caches_async()

    def _rebuild_caches_async(self):
        """
        Renders, in the background, whatever cache files the sounds are
        missing or have outdated — sounds imported before the effects
        pipeline existed, and every sound after the secondary volume
        changes. Doing it here means playback never has to render anything
        on the critical path.
        """
        sounds = list(self.config.get("sounds", []))
        if not sounds or self._cache_rebuild_running:
            return
        self._cache_rebuild_running = True

        def worker():
            rendered = 0
            for sound in sounds:
                try:
                    if ensure_caches(sound, self.config, "downloads"):
                        rendered += 1
                except Exception:
                    pass
            self.caches_ready.emit(rendered)

        threading.Thread(target=worker, daemon=True).start()

    @Slot(int)
    def _on_caches_ready(self, rendered):
        self._cache_rebuild_running = False
        if not rendered:
            return
        config_manager.save_config(self.config)
        self.library_view.refresh()

    def _switch_tab(self, index):
        self.stacked_widget.setCurrentIndex(index)
        self.btn_lib.setChecked(index == 0)
        self.btn_set.setChecked(index == 1)

    def _play_sound(self, sound):
        playback_file = resolve_playback_file(sound)
        if not playback_file:
            return

        # Both routes carry the same baked effects; the secondary one is a
        # pre-rendered attenuated copy, so nothing is computed at click time.
        filepath_sec = resolve_secondary_file(sound)

        # Solo cuts everything else — but never the sound being toggled,
        # or pausing it would drop its position and restart from zero.
        focused = self.audio_manager.focused_info
        same_sound = focused and focused.get("sound_id") == sound.get("id")
        if self.config.get("mode_solo", False) and not same_sound:
            self.audio_manager.stop_all()

        self.audio_manager.set_fade_durations(
            sound.get("fade_in_ms", self.config.get("fade_in_ms", 150)),
            sound.get("fade_out_ms", self.config.get("fade_out_ms", 150)),
        )

        self.audio_manager.toggle_play_pause(
            filepath_primary=playback_file,
            filepath_secondary=filepath_sec,
            name=sound.get("name", "Unknown"),
            volume=1.0,
            primary_device_name=self.config.get("primary_output"),
            secondary_device_name=self.config.get("secondary_output"),
            dual_enabled=self.config.get("dual_output_enabled", False),
            sound_id=sound.get("id"),
        )

    def _on_seek(self, ratio):
        fi = self.audio_manager.focused_info
        if fi and fi.get("duration"):
            self.audio_manager.seek_focused(ratio * fi["duration"])

    def _update_timeline(self):
        prog = self.audio_manager.get_focused_progress()
        if not prog:
            self._release_card(self._last_timeline_sound_id)
            self._last_timeline_sound_id = None
            self.player_bar.update_progress("", 0, 0, None)
            return

        sound_id = prog.get("sound_id")
        peaks = None
        if sound_id != self._last_timeline_sound_id:
            self._release_card(self._last_timeline_sound_id)

        card = self.library_view.cards.get(sound_id)
        if card:
            if prog["duration"] > 0:
                card.set_playback_progress(prog["current"] / prog["duration"])
            card.set_playing_state("paused" if prog["is_paused"] else "playing")

        if sound_id != self._last_timeline_sound_id:
            self._last_timeline_sound_id = sound_id
            if card:
                peaks = card.waveform.peaks
            # else: sound not currently rendered (filtered/scrolled out of view) -
            # leave peaks as None and let the player bar keep its last-known peaks.

        self.player_bar.update_progress(
            prog["name"], prog["current"], prog["duration"], peaks, prog["is_paused"]
        )

    def _release_card(self, sound_id):
        """Puts a card's button back to PLAY once it is no longer the sound
        the transport is following."""
        card = self.library_view.cards.get(sound_id)
        if card:
            card.set_playing_state("idle")
            card.set_playback_progress(0.0)

    def _panic_stop(self):
        self.audio_manager.stop_all()
        self._release_card(self._last_timeline_sound_id)
        self._last_timeline_sound_id = None

    def _refresh_panic_hint(self):
        key = self.config.get("panic_hotkey", "None")
        self.lbl_panic_hint.setText(
            "" if key in (None, "None") else f"ou la touche {key.upper()}"
        )

    def _bind_hotkey(self, sound_id, btn):
        btn.setText("Press key...")

        def capture():
            hk = keyboard.read_hotkey(suppress=False)
            self._apply_hotkey(hk, sound_id)

        self.hotkey_manager.shutdown()
        threading.Thread(target=capture, daemon=True).start()

    def _apply_hotkey(self, hk, sound_id):
        def apply():
            for s in self.library_view.sounds:
                if s["id"] == sound_id:
                    s["hotkey"] = "None" if hk == "esc" else hk
            self.config["sounds"] = self.library_view.sounds
            config_manager.save_config(self.config)
            self.hotkey_manager.load_hotkeys(self.config)
            self.library_view.refresh()
        QTimer.singleShot(0, apply)

    def _bind_panic_key(self):
        self.settings_view.set_panic_label("Appuyez sur une touche...")

        def capture():
            hk = keyboard.read_hotkey(suppress=False)
            self._apply_panic_key(hk)

        self.hotkey_manager.shutdown()
        threading.Thread(target=capture, daemon=True).start()

    def _apply_panic_key(self, hk):
        def apply():
            self.config["panic_hotkey"] = "None" if hk == "esc" else hk
            config_manager.save_config(self.config)
            self.hotkey_manager.load_hotkeys(self.config)
            self.settings_view.set_panic_label(self.config["panic_hotkey"])
            self._refresh_panic_hint()
        QTimer.singleShot(0, apply)

    def _on_settings_saved(self, config):
        self.config = config
        config_manager.save_config(config)
        self.audio_manager.set_fade_durations(
            config.get("fade_in_ms", 150), config.get("fade_out_ms", 150)
        )
        self.hotkey_manager.load_hotkeys(config)
        # The secondary volume may have moved: re-bake the cable renders.
        self._rebuild_caches_async()

    def _on_sounds_changed(self):
        self.hotkey_manager.load_hotkeys(self.config)
