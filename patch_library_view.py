import os
import re

with open("ui/views/library_view.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update _DropGrid to accept URLs
dropgrid_old = """    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(SoundCard.MIME_TYPE):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(SoundCard.MIME_TYPE):
            event.acceptProposedAction()

    def dropEvent(self, event):
        data = event.mimeData().data(SoundCard.MIME_TYPE)
        if not data:
            return
        self._on_drop(bytes(data).decode("utf-8"), event.position().toPoint())"""

dropgrid_new = """    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(SoundCard.MIME_TYPE) or event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(SoundCard.MIME_TYPE) or event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            urls = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
            if hasattr(self.parent(), "add_sounds_from_files"):
                self.parent().add_sounds_from_files(urls)
            return

        data = event.mimeData().data(SoundCard.MIME_TYPE)
        if not data:
            return
        self._on_drop(bytes(data).decode("utf-8"), event.position().toPoint())"""

content = content.replace(dropgrid_old, dropgrid_new)

# 2. Update Signal add_sound_done to add_sounds_done = Signal(list)
content = content.replace("add_sound_done = Signal(str, dict)", "add_sounds_done = Signal(list)")
content = content.replace("self.add_sound_done.connect(self._on_add_sound_done)", "self.add_sounds_done.connect(self._on_add_sounds_done)")

# 3. Update add_sound method
add_sound_old = """    def add_sound(self):
        f, _ = QFileDialog.getOpenFileName(
            self, tr("library.pick_file"), "", tr("library.audio_filter"),
            options=QFileDialog.DontUseNativeDialog
        )
        if not f:
            return

        sid = str(uuid.uuid4())[:8]
        name = os.path.basename(f)

        self.progress_dialog = QProgressDialog(tr("library.importing"), None, 0, 0, self)
        self.progress_dialog.setWindowTitle(tr("common.please_wait"))
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setCancelButton(None)
        self.progress_dialog.show()

        def process():
            try:
                proc_path = normalize_and_import_audio(f, paths.downloads_dir(), sid)
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
            QMessageBox.critical(self, tr("common.error"), tr("library.import_failed"))"""

add_sound_new = """    def add_sound(self):
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
            QMessageBox.critical(self, tr("common.error"), tr("library.import_failed"))"""

content = content.replace(add_sound_old, add_sound_new)

with open("ui/views/library_view.py", "w", encoding="utf-8") as f:
    f.write(content)

print("library_view.py updated!")
