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
from audio_processor import (
    generate_and_save_peaks, generate_effects_cache, normalize_and_import_audio
)
from ui.theme import get_icon
from ui.views.sound_edit_dialog import SoundEditDialog
from ui.widgets.sound_card import SoundCard
from yt_downloader import download_youtube_audio_async


class LibraryView(QWidget):
    sound_played = Signal(dict)
    hotkey_bind_requested = Signal(str, object)
    add_sound_done = Signal(str, dict)
    effects_rendered = Signal(str, str)
    sounds_changed = Signal()

    def __init__(self, config, audio_manager, parent=None):
        super().__init__(parent)
        self.config = config
        self.audio_manager = audio_manager
        self.sounds = self.config.get("sounds", [])
        self.filtered_sounds = list(self.sounds)
        self.cards = {}
        self._build()
        self.add_sound_done.connect(self._on_add_sound_done)
        self.effects_rendered.connect(self._on_effects_rendered)
        self._rebuild_grid()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        topbar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher un son (Titre, Touche, Catégorie)...")
        self.search_input.setFixedHeight(36)
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._filter_sounds)
        self.search_input.textChanged.connect(lambda _t: self.search_timer.start(300))
        topbar.addWidget(self.search_input)

        btn_add = QPushButton(" IMPORT LOCAL")
        btn_add.setIcon(get_icon("add.svg"))
        btn_add.setFixedHeight(36)
        btn_add.clicked.connect(self.add_sound)
        topbar.addWidget(btn_add)

        btn_yt = QPushButton(" YT DOWNLOAD")
        btn_yt.setIcon(get_icon("download.svg"))
        btn_yt.setProperty("class", "accent")
        btn_yt.setFixedHeight(36)
        btn_yt.clicked.connect(self.download_youtube)
        topbar.addWidget(btn_yt)

        layout.addLayout(topbar)
        layout.addSpacing(10)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.grid_layout = QGridLayout(self.scroll_widget)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(15)
        self.scroll_area.setWidget(self.scroll_widget)
        layout.addWidget(self.scroll_area)

        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self._rebuild_grid)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resize_timer.start(150)

    def refresh(self):
        self.sounds = self.config.get("sounds", [])
        self._filter_sounds()

    def _filter_sounds(self):
        term = self.search_input.text().lower()
        self.filtered_sounds = [
            s for s in self.sounds
            if term in s.get("name", "").lower()
            or term in (s.get("hotkey") or "").lower()
            or term in (s.get("color") or "").lower()
        ]
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

        width = self.scroll_area.viewport().width()
        card_width = 320
        cols = max(1, width // (card_width + 15))

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

        self.grid_layout.setRowStretch(self.grid_layout.rowCount(), 1)

    def _empty_state(self):
        if self.sounds:
            text = "Aucun son ne correspond à cette recherche."
        else:
            text = (
                "Votre bibliothèque est vide.\n\n"
                "Importez un fichier audio, ou collez une URL YouTube pour "
                "télécharger un son directement."
            )
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

        def worker():
            try:
                path = generate_effects_cache(draft, "downloads")
            except Exception:
                path = ""
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
            self, "Confirmation", "Êtes-vous sûr de vouloir supprimer ce son ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.No:
            return
        self.sounds = [s for s in self.sounds if s["id"] != sound_id]
        self._persist()
        self.refresh()

    def _persist(self):
        self.config["sounds"] = self.sounds
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
            sound["cached_effects_file"] = generate_effects_cache(sound, "downloads")
        except Exception:
            sound["cached_effects_file"] = None
        return sound

    def add_sound(self):
        f, _ = QFileDialog.getOpenFileName(
            self, "Sélectionner un fichier audio", "",
            "Audio Files (*.mp3 *.wav *.ogg *.flac *.m4a)",
            options=QFileDialog.DontUseNativeDialog
        )
        if not f:
            return

        sid = str(uuid.uuid4())[:8]
        name = os.path.basename(f)

        self.progress_dialog = QProgressDialog("Importation et normalisation en cours...", None, 0, 0, self)
        self.progress_dialog.setWindowTitle("Veuillez patienter")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setCancelButton(None)
        self.progress_dialog.show()

        def process():
            try:
                proc_path = normalize_and_import_audio(f, "downloads", sid)
                sound = self._new_sound(sid, name, proc_path, "Gris", self.config)
            except Exception:
                sound = {}
            self.add_sound_done.emit("", sound)

        threading.Thread(target=process, daemon=True).start()

    @Slot(str, dict)
    def _on_add_sound_done(self, _unused, new_sound):
        if hasattr(self, "progress_dialog") and self.progress_dialog:
            self.progress_dialog.close()

        if new_sound.get("filename"):
            self.sounds.insert(0, new_sound)
            self._persist()
            self.refresh()
        else:
            QMessageBox.critical(self, "Erreur", "Échec de l'import du fichier audio.")

    def download_youtube(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Télécharger YouTube")
        dlg.setFixedSize(400, 200)

        layout = QVBoxLayout(dlg)
        url_input = QLineEdit()
        url_input.setPlaceholderText("URL YouTube (https://...)")
        layout.addWidget(url_input)

        title_input = QLineEdit()
        title_input.setPlaceholderText("Nom du son (optionnel)")
        layout.addWidget(title_input)

        pb = QProgressBar()
        pb.setValue(0)
        layout.addWidget(pb)

        btn_dl = QPushButton("TÉLÉCHARGER")
        btn_dl.setProperty("class", "accent")
        layout.addWidget(btn_dl)

        class YTSignals(QObject):
            progress = Signal(int)
            done = Signal(bool, list, str)

        sigs = YTSignals()
        sigs.progress.connect(pb.setValue)

        def start_dl():
            url = url_input.text().strip()
            if not url:
                return
            btn_dl.setEnabled(False)

            def prog_cb(pct_str, curr, tot, t):
                try:
                    pct = float(pct_str.replace("%", "").strip())
                    sigs.progress.emit(int(pct))
                except ValueError:
                    pass

            def done_cb(succ, res, err):
                sigs.done.emit(succ, res or [], err)

            download_youtube_audio_async(url, "downloads", done_cb, prog_cb)

        def finish(succ, res, err):
            dlg.accept()
            if succ and res:
                for filepath, yt_title in res:
                    sid = str(uuid.uuid4())[:8]
                    self.sounds.insert(0, self._new_sound(
                        sid, title_input.text() or yt_title, filepath, "Musiques", self.config
                    ))
                self._persist()
                self.refresh()
            else:
                QMessageBox.critical(self, "Erreur", f"Échec: {err}")

        sigs.done.connect(finish)
        btn_dl.clicked.connect(start_dl)
        dlg.exec()
