import os
import threading
import uuid

from PySide6.QtCore import Qt, QObject, QTimer, Signal, Slot
from PySide6.QtWidgets import (
    QDialog, QFileDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QProgressBar, QProgressDialog, QPushButton, QScrollArea,
    QVBoxLayout, QWidget
)

import config_manager
import errors
import paths
import profiles
from hotkey_manager import HotkeyManager
from i18n import category_label, tr
from audio_processor import (
    generate_and_save_peaks, generate_effects_cache, normalize_and_import_audio
)
from ui.theme import CATEGORY_COLORS, get_icon
from ui.views.sound_edit_dialog import SoundEditDialog
from ui.views.youtube_dialog import YoutubeDialog
from ui.widgets.sound_card import SoundCard


class _DropGrid(QWidget):
    """The grid container, accepting a card dropped onto it and reporting
    where it landed."""

    def __init__(self, on_drop, on_files_dropped=None, parent=None):
        super().__init__(parent)
        self._on_drop = on_drop
        self._on_files_dropped = on_files_dropped
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(SoundCard.MIME_TYPE) or event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(SoundCard.MIME_TYPE) or event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            urls = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
            if self._on_files_dropped:
                self._on_files_dropped(urls)
            return

        data = event.mimeData().data(SoundCard.MIME_TYPE)
        if not data:
            return
        self._on_drop(bytes(data).decode("utf-8"), event.position().toPoint())
        event.acceptProposedAction()


class LibraryView(QWidget):
    sound_played = Signal(dict)
    hotkey_bind_requested = Signal(str, object)
    add_sounds_done = Signal(list)
    effects_rendered = Signal(str, str)
    sounds_changed = Signal()

    CARD_SPACING = 15

    def __init__(self, config, audio_manager, parent=None):
        super().__init__(parent)
        self.config = config
        self.audio_manager = audio_manager
        self.sounds = profiles.active_sounds(self.config)
        self.filtered_sounds = list(self.sounds)
        self.cards = {}
        self.category_filter = None
        self._build()
        self.add_sounds_done.connect(self._on_add_sounds_done)
        self.effects_rendered.connect(self._on_effects_rendered)
        self._filter_sounds()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        topbar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(tr("library.search"))
        self.search_input.setFixedHeight(36)
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._filter_sounds)
        self.search_input.textChanged.connect(lambda _t: self.search_timer.start(300))
        topbar.addWidget(self.search_input)

        btn_add = QPushButton(tr("library.import"))
        btn_add.setIcon(get_icon("add.svg"))
        btn_add.setFixedHeight(36)
        btn_add.clicked.connect(self.add_sound)
        topbar.addWidget(btn_add)

        btn_yt = QPushButton(tr("library.youtube"))
        btn_yt.setIcon(get_icon("download.svg"))
        btn_yt.setProperty("class", "accent")
        btn_yt.setFixedHeight(36)
        btn_yt.clicked.connect(self.download_youtube)
        topbar.addWidget(btn_yt)

        layout.addLayout(topbar)

        self.filter_row = QHBoxLayout()
        self.filter_row.setSpacing(6)
        layout.addLayout(self.filter_row)
        layout.addSpacing(10)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = _DropGrid(self._on_card_dropped, self.add_sounds_from_files)
        self.grid_layout = QGridLayout(self.scroll_widget)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(self.CARD_SPACING)
        self.scroll_area.setWidget(self.scroll_widget)
        layout.addWidget(self.scroll_area)

        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self._rebuild_grid)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resize_timer.start(150)

    def _rebuild_filters(self):
        """One chip per category actually in use — an empty category is not
        a filter worth offering."""
        while self.filter_row.count():
            item = self.filter_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        used = [c for c in CATEGORY_COLORS if any(
            s.get("color", "Gris") == c for s in self.sounds)]
        if not used:
            return

        for key in [None] + used:
            label = tr("library.filter_all") if key is None else category_label(key)
            chip = QPushButton(label)
            chip.setCheckable(True)
            chip.setChecked(self.category_filter == key)
            chip.setFixedHeight(26)
            if key is not None:
                chip.setStyleSheet(f"border: 1px solid {CATEGORY_COLORS[key]};")
            chip.clicked.connect(lambda _=False, k=key: self._set_category_filter(k))
            self.filter_row.addWidget(chip)
        self.filter_row.addStretch()

    def _set_category_filter(self, key):
        self.category_filter = None if key == self.category_filter else key
        self._filter_sounds()

    def _card_at(self, position):
        for sound_id, card in self.cards.items():
            if card.geometry().contains(position):
                return sound_id
        return None

    def move_sound(self, sound_id, target_id):
        """
        Puts `sound_id` where `target_id` currently sits. The list order is
        the displayed order, in the Library and in Scene alike. Returns True
        if anything moved.
        """
        if not target_id or target_id == sound_id:
            return False

        source = next((s for s in self.sounds if s["id"] == sound_id), None)
        if source is None or not any(s["id"] == target_id for s in self.sounds):
            return False

        self.sounds.remove(source)
        target_index = next(i for i, s in enumerate(self.sounds) if s["id"] == target_id)
        self.sounds.insert(target_index, source)
        self._persist()
        self.refresh()
        return True

    def _on_card_dropped(self, sound_id, position):
        self.move_sound(sound_id, self._card_at(position))

    def refresh(self):
        self.sounds = profiles.active_sounds(self.config)
        self._filter_sounds()

    def _filter_sounds(self):
        term = self.search_input.text().lower()
        self.filtered_sounds = [
            s for s in self.sounds
            if (self.category_filter is None
                or s.get("color", "Gris") == self.category_filter)
            and (term in s.get("name", "").lower()
                 or term in (s.get("hotkey") or "").lower()
                 or term in (s.get("color") or "").lower())
        ]
        self._rebuild_filters()
        self._rebuild_grid()

    def _rebuild_grid(self):
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not self.filtered_sounds:
            self.grid_layout.addWidget(self._empty_state(), 0, 0)
            self.grid_layout.setRowStretch(1, 1)
            self.cards = {}
            return

        # Only add a column when a whole card genuinely fits: a cramped
        # two-column grid is worse than a clean single column.
        width = self.scroll_area.viewport().width()
        step = SoundCard.WIDTH + self.CARD_SPACING
        cols = max(1, (width + self.CARD_SPACING) // step)

        self.cards = {}
        for i, sound in enumerate(self.filtered_sounds):
            row, col = divmod(i, cols)
            card = SoundCard(sound)
            card.play_requested.connect(self._on_play)
            card.edit_requested.connect(self._on_edit)
            card.delete_requested.connect(self.remove_sound)
            card.hotkey_requested.connect(self.hotkey_bind_requested)
            card.volume_changed.connect(self._on_volume_changed)
            card.color_changed.connect(self._on_color_changed)
            self.cards[sound["id"]] = card
            self.grid_layout.addWidget(card, row, col)

        conflicts = HotkeyManager.find_conflicts(self.sounds)
        for hotkey, clashing in conflicts.items():
            for sound in clashing:
                card = self.cards.get(sound["id"])
                if card:
                    card.set_hotkey_conflict(
                        [s.get("name", "") for s in clashing if s["id"] != sound["id"]]
                    )

        self.grid_layout.setRowStretch(self.grid_layout.rowCount(), 1)

    def _empty_state(self):
        if self.sounds:
            text = tr("library.empty_search")
        else:
            text = tr("library.empty")
        label = QLabel(text)
        label.setObjectName("EmptyState")
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)
        return label

    def _on_play(self, sound_id):
        sound = next((s for s in self.sounds if s["id"] == sound_id), None)
        if sound:
            self.sound_played.emit(sound)

    def _on_edit(self, sound_id):
        sound = next((s for s in self.sounds if s["id"] == sound_id), None)
        if not sound:
            return
        # Editing re-renders the sound's cache files, which cannot be
        # overwritten while they are being streamed.
        self.audio_manager.stop_sound(sound_id)
        dlg = SoundEditDialog(sound, self.config, self.audio_manager, self)
        if dlg.exec() == QDialog.Accepted:
            self._persist()
            self.refresh()

    def _on_volume_changed(self, sound_id, value):
        sound = next((s for s in self.sounds if s["id"] == sound_id), None)
        if not sound:
            return
        sound["volume"] = value
        self._persist()
        self._rerender_effects(sound)

    def _rerender_effects(self, sound):
        """
        Re-bakes the effects cache after a quick edit on the card, in the
        background. Playback streams that file, so leaving it stale would
        make the change silently ineffective — the very bug this feature
        exists to fix.
        """
        draft = dict(sound)
        sound_id = sound["id"]
        # Same reason as _on_edit: free the file before FFmpeg rewrites it.
        self.audio_manager.stop_sound(sound_id)

        def worker():
            try:
                path = generate_effects_cache(draft, paths.downloads_dir())
            except Exception as exc:
                path = ""
                errors.report(tr("library.import_failed"), exc)
            self.effects_rendered.emit(sound_id, path)

        threading.Thread(target=worker, daemon=True).start()

    @Slot(str, str)
    def _on_effects_rendered(self, sound_id, path):
        if not path:
            return
        for s in self.sounds:
            if s["id"] == sound_id:
                s["cached_effects_file"] = path
                break
        self._persist()
        self.refresh()

    def _on_color_changed(self, sound_id, color):
        for s in self.sounds:
            if s["id"] == sound_id:
                s["color"] = color
                break
        self._persist()
        self.refresh()

    def remove_sound(self, sound_id):
        reply = QMessageBox.question(
            self, tr("common.confirm"), tr("library.delete_body"),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.No:
            return
        self.sounds = [s for s in self.sounds if s["id"] != sound_id]
        self._persist()
        self.refresh()

    def _persist(self):
        config_manager.save_config(self.config)
        self.sounds_changed.emit()

    @staticmethod
    def _new_sound(sid, name, filepath, color, config):
        """
        Builds a complete sound dict and renders its effects cache once, so
        every sound has a valid cached_effects_file from the moment it is
        created — playback never needs a fallback path.
        """
        sound = {
            "id": sid, "name": name, "filename": filepath,
            "hotkey": "None", "color": color,
            "fade_in_ms": config.get("fade_in_ms", 150),
            "fade_out_ms": config.get("fade_out_ms", 150),
        }
        sound.update(config_manager.SOUND_EFFECT_DEFAULTS)
        try:
            generate_and_save_peaks(filepath)
        except Exception:
            pass
        try:
            sound["cached_effects_file"] = generate_effects_cache(sound, paths.downloads_dir())
        except Exception as exc:
            # Swallowing this used to leave a sound that silently ignored its
            # own settings, with no way for the user to know why.
            sound["cached_effects_file"] = None
            errors.report(tr("library.import_failed"), exc)
        return sound

    def add_sound(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, tr("library.pick_file"), "", tr("library.audio_filter"),
            options=QFileDialog.DontUseNativeDialog
        )
        self.add_sounds_from_files(files)

    def add_sounds_from_files(self, files):
        if not files:
            return

        self.progress_dialog = QProgressDialog(tr("library.importing"), None, 0, len(files), self)
        self.progress_dialog.setWindowTitle(tr("common.please_wait"))
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setCancelButton(None)
        self.progress_dialog.setValue(0)
        self.progress_dialog.show()

        def process():
            results = []
            for i, f in enumerate(files):
                sid = str(uuid.uuid4())[:8]
                name = os.path.basename(f)
                try:
                    proc_path = normalize_and_import_audio(f, paths.downloads_dir(), sid)
                    sound = self._new_sound(sid, name, proc_path, "Gris", self.config)
                    results.append(sound)
                except Exception:
                    pass
            self.add_sounds_done.emit(results)

        threading.Thread(target=process, daemon=True).start()

    @Slot(list)
    def _on_add_sounds_done(self, new_sounds):
        if hasattr(self, "progress_dialog") and self.progress_dialog:
            self.progress_dialog.close()

        if new_sounds:
            # Reverse to insert them in the order they were selected
            for s in reversed(new_sounds):
                self.sounds.insert(0, s)
            self._persist()
            self.refresh()
        else:
            QMessageBox.critical(self, tr("common.error"), tr("library.import_failed"))

    def download_youtube(self):
        dialog = YoutubeDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        for filepath, yt_title in dialog.results:
            sid = str(uuid.uuid4())[:8]
            self.sounds.insert(0, self._new_sound(
                sid, dialog.chosen_name() or yt_title, filepath, "Musiques", self.config
            ))
        self._persist()
        self.refresh()
