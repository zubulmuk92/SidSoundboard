import os

with open("ui/views/library_view.py", "r", encoding="utf-8") as f:
    content = f.read()

drop_old = """class _DropGrid(QWidget):
    \"\"\"The grid container, accepting a card dropped onto it and reporting
    where it landed.\"\"\"

    def __init__(self, on_drop, parent=None):
        super().__init__(parent)
        self._on_drop = on_drop
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
            if hasattr(self.parent(), "add_sounds_from_files"):
                self.parent().add_sounds_from_files(urls)
            return

        data = event.mimeData().data(SoundCard.MIME_TYPE)
        if not data:
            return
        self._on_drop(bytes(data).decode("utf-8"), event.position().toPoint())
        event.acceptProposedAction()"""

drop_new = """class _DropGrid(QWidget):
    \"\"\"The grid container, accepting a card dropped onto it and reporting
    where it landed.\"\"\"

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
        event.acceptProposedAction()"""

content = content.replace(drop_old, drop_new)

init_old = """        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = _DropGrid(self._on_card_dropped)
        self.grid_layout = QGridLayout(self.scroll_widget)"""

init_new = """        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = _DropGrid(self._on_card_dropped, self.add_sounds_from_files)
        self.grid_layout = QGridLayout(self.scroll_widget)"""

content = content.replace(init_old, init_new)

with open("ui/views/library_view.py", "w", encoding="utf-8") as f:
    f.write(content)

print("library_view.py drag and drop fixed")
