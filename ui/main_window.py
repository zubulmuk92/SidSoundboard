import threading

import keyboard
from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QInputDialog, QLabel, QMainWindow,
    QPushButton, QStackedWidget, QVBoxLayout, QWidget
)

import config_manager
import i18n
import profiles
from i18n import tr
import paths
from audio_processor import ensure_caches, resolve_playback_file, resolve_secondary_file
from ui.theme import QSS, TEXT_MAIN, get_icon, resource_path
import errors
from ui.views.library_view import LibraryView
from ui.views.scene_view import SceneView
from ui.views.settings_view import SettingsView
from ui.views.welcome_view import WelcomeView
from ui.widgets.player_bar import PlayerBar
from ui.widgets.waveform import load_peaks


class AppGUI(QMainWindow):
    caches_ready = Signal(int)

    def __init__(self, audio_manager, hotkey_manager, config):
        super().__init__()
        self._cache_rebuild_running = False
        self.caches_ready.connect(self._on_caches_ready)
        errors.reporter.reported.connect(self._on_error_reported)
        self.audio_manager = audio_manager
        self.hotkey_manager = hotkey_manager
        self.config = config
        self._last_timeline_sound_id = None
        self._active_tab = 0
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
        self._rebuild_caches_async()

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

        # The scene selector sits above navigation: switching scene is a
        # change of context for the whole app, not a setting among others.
        # It is labelled, and the create action spells itself out - a bare
        # "+" with a tooltip left people hunting for where scenes are made.
        scene_block = QWidget()
        scene_layout = QVBoxLayout(scene_block)
        scene_layout.setContentsMargins(20, 0, 20, 0)
        scene_layout.setSpacing(4)

        scene_caption = QLabel(tr("scene.label").upper())
        scene_caption.setObjectName("SidebarCaption")
        scene_layout.addWidget(scene_caption)

        self.cb_profile = QComboBox()
        self.cb_profile.setToolTip(tr("scene.hint"))
        self.cb_profile.currentIndexChanged.connect(self._on_profile_selected)
        scene_layout.addWidget(self.cb_profile)

        btn_new_profile = QPushButton(tr("scene.new"))
        btn_new_profile.setObjectName("NewSceneButton")
        btn_new_profile.setToolTip(tr("scene.hint"))
        btn_new_profile.clicked.connect(self._create_profile)
        scene_layout.addWidget(btn_new_profile)

        side_layout.addWidget(scene_block)
        side_layout.addSpacing(20)

        self.nav_buttons = []
        for index, (key, icon) in enumerate((
            ("nav.pads", "play.svg"),
            ("nav.library", "lib.svg"),
            ("nav.settings", "settings.svg"),
            ("nav.help", "add.svg"),
        )):
            button = QPushButton(tr(key))
            button.setIcon(get_icon(icon))
            button.setCheckable(True)
            button.clicked.connect(lambda _=False, i=index: self._switch_tab(i))
            side_layout.addWidget(button)
            self.nav_buttons.append(button)

        side_layout.addStretch()

        btn_stop = QPushButton(tr("panic.button"))
        btn_stop.setObjectName("PanicButton")
        btn_stop.setFixedHeight(54)
        btn_stop.setCursor(Qt.PointingHandCursor)
        btn_stop.setToolTip(tr("panic.tooltip"))
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

        self.scene_view = SceneView(self.config)
        self.scene_view.sound_triggered.connect(self._on_scene_trigger)
        self.stacked_widget.addWidget(self.scene_view)

        self.library_view = LibraryView(self.config, self.audio_manager)
        self.library_view.sound_played.connect(self._play_sound)
        self.library_view.hotkey_bind_requested.connect(self._bind_hotkey)
        self.library_view.sounds_changed.connect(self._on_sounds_changed)
        self.stacked_widget.addWidget(self.library_view)

        self.settings_view = SettingsView(
            self.audio_manager, self.config, self._on_settings_saved, self._bind_panic_key,
            on_scenes_changed=self._on_scenes_changed,
        )
        self.stacked_widget.addWidget(self.settings_view)

        self.welcome_view = WelcomeView(self.audio_manager, self.config)
        self.welcome_view.open_settings.connect(lambda: self._switch_tab(2))
        self.welcome_view.open_library.connect(lambda: self._switch_tab(1))
        self.stacked_widget.addWidget(self.welcome_view)

        self.error_banner = QLabel()
        self.error_banner.setObjectName("ErrorBanner")
        self.error_banner.setWordWrap(True)
        self.error_banner.hide()
        content_layout.addWidget(self.error_banner)

        self.player_bar = PlayerBar()
        self.player_bar.seek_requested.connect(self._on_seek)
        self.player_bar.skip_requested.connect(self._on_skip)
        self.player_bar.mode_changed.connect(self._on_play_mode_changed)
        content_layout.addWidget(self.player_bar)
        self._refresh_profile_combo()
        self._switch_tab(self._active_tab)

    def _rebuild_caches_async(self):
        """
        Renders, in the background, whatever cache files the sounds are
        missing or have outdated — sounds imported before the effects
        pipeline existed, and every sound after the secondary volume
        changes. Doing it here means playback never has to render anything
        on the critical path.
        """
        sounds = list(profiles.all_sounds(self.config))
        if not sounds or self._cache_rebuild_running:
            return
        self._cache_rebuild_running = True

        def worker():
            rendered = 0
            for sound in sounds:
                try:
                    if ensure_caches(sound, self.config, paths.downloads_dir()):
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

    def _refresh_profile_combo(self):
        self.cb_profile.blockSignals(True)
        self.cb_profile.clear()
        for profile in self.config["profiles"]:
            self.cb_profile.addItem(profile["name"], profile["id"])
        active = profiles.active_profile(self.config)["id"]
        index = self.cb_profile.findData(active)
        if index >= 0:
            self.cb_profile.setCurrentIndex(index)
        self.cb_profile.blockSignals(False)
        settings = getattr(self, "settings_view", None)
        if settings is not None:
            settings.refresh_scenes()

    def _on_profile_selected(self, index):
        profile_id = self.cb_profile.itemData(index)
        if not profile_id or profile_id == self.config.get("active_profile"):
            return
        profiles.set_active(self.config, profile_id)
        config_manager.save_config(self.config)
        self.audio_manager.stop_all()
        self.hotkey_manager.load_hotkeys(self.config)
        self.library_view.refresh()
        self.scene_view.refresh()

    def _create_profile(self):
        name, ok = QInputDialog.getText(self, tr("scene.new"), tr("scene.new_prompt"))
        if not ok or not name.strip():
            return
        created = profiles.create_profile(self.config, name.strip())
        profiles.set_active(self.config, created["id"])
        config_manager.save_config(self.config)
        self._refresh_profile_combo()
        self.hotkey_manager.load_hotkeys(self.config)
        self.library_view.refresh()
        self.scene_view.refresh()

    def _on_scenes_changed(self):
        """A scene was renamed or deleted from the Settings screen."""
        config_manager.save_config(self.config)
        self._refresh_profile_combo()
        self.hotkey_manager.load_hotkeys(self.config)
        self.library_view.refresh()
        self.scene_view.refresh()

    def _on_scene_trigger(self, sound_id):
        for sound in profiles.active_sounds(self.config):
            if sound["id"] == sound_id:
                self._play_sound(sound)
                return

    @Slot(str)
    def _on_error_reported(self, message):
        self.error_banner.setText(message)
        self.error_banner.show()
        QTimer.singleShot(8000, self.error_banner.hide)

    def _switch_tab(self, index):
        self._active_tab = index
        self.stacked_widget.setCurrentIndex(index)
        for position, button in enumerate(self.nav_buttons):
            button.setChecked(position == index)
        if index == 0:
            self.scene_view.refresh()
        elif index == 3:
            self.welcome_view.refresh()

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
            loop=sound.get("loop", False),
        )

    def _on_seek(self, ratio):
        fi = self.audio_manager.focused_info
        if fi and fi.get("duration"):
            self.audio_manager.seek_focused(ratio * fi["duration"])

    def _on_skip(self):
        self.audio_manager.play_next()

    @Slot(str)
    def _on_play_mode_changed(self, mode):
        self.audio_manager.play_mode = mode

    def _update_timeline(self):
        prog = self.audio_manager.get_focused_progress()
        if not prog:
            self._release_card(self._last_timeline_sound_id)
            self._last_timeline_sound_id = None
            self.scene_view.set_playing(None, 0.0)
            self.player_bar.update_progress("", 0, 0, None, False, 0)
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

        ratio = prog["current"] / prog["duration"] if prog["duration"] > 0 else 0.0
        self.scene_view.set_playing(sound_id, ratio)
        self.player_bar.update_progress(
            prog["name"], prog["current"], prog["duration"], peaks, prog["is_paused"], len(self.audio_manager.playback_queue)
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
            "" if key in (None, "None") else tr("panic.hint", key=key.upper())
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
            for s in profiles.active_sounds(self.config):
                if s["id"] == sound_id:
                    s["hotkey"] = "None" if hk == "esc" else hk
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
        language_changed = config.get("language", i18n.DEFAULT_LANGUAGE) != i18n.get_language()
        self.config = config
        config_manager.save_config(config)
        if language_changed:
            i18n.set_language(config["language"])
            # Deferred: rebuilding destroys the settings view whose _save()
            # is still on the stack right now.
            QTimer.singleShot(0, self._build_ui)
        self.audio_manager.set_fade_durations(
            config.get("fade_in_ms", 150), config.get("fade_out_ms", 150)
        )
        self.hotkey_manager.load_hotkeys(config)
        # The secondary volume may have moved: re-bake the cable renders.
        self._rebuild_caches_async()

    def _on_sounds_changed(self):
        self.hotkey_manager.load_hotkeys(self.config)
