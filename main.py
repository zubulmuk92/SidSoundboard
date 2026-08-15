import sys
import os

if "--yt-worker" in sys.argv:
    idx = sys.argv.index("--yt-worker")
    from yt_downloader import run_worker
    run_worker(sys.argv[idx + 1], sys.argv[idx + 2])
    sys.exit(0)

import traceback

def log_crash(exctype, value, tb):
    with open("crash.log", "w") as f:
        traceback.print_exception(exctype, value, tb, file=f)
sys.excepthook = log_crash

# FIX for static-ffmpeg in PyInstaller (--noconsole)
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')

import i18n
from config_manager import load_config
from audio_manager import AudioManager
from hotkey_manager import HotkeyManager
from ui.main_window import AppGUI
from ui.theme import resource_path
import cache_manager

def main():
    if sys.stdout is None:
        sys.stdout = open(os.devnull, 'w')
    if sys.stderr is None:
        sys.stderr = open(os.devnull, 'w')

    cache_manager.cleanup_caches()

    config = load_config()
    i18n.set_language(config.get("language", i18n.DEFAULT_LANGUAGE))

    audio_manager = AudioManager()

    hotkey_manager = HotkeyManager(audio_manager, config)
    hotkey_manager.load_hotkeys(config)

    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QIcon

    qt_app = QApplication.instance()
    if not qt_app:
        qt_app = QApplication(sys.argv)

    qt_app.setWindowIcon(QIcon(resource_path("logo.ico")))

    app = AppGUI(audio_manager, hotkey_manager, config)

    # Configuration du System Tray
    import pystray
    from PIL import Image
    import threading

    def build_tray_image(size=64):
        """
        Squares up the transparent logo for the tray.

        logo_sq.png is a fully opaque square, so it shows as a coloured tile
        next to the other tray icons. logo.png is properly cut out but
        rectangular, and a tray icon is square — pasting it straight in
        would stretch it. So: crop to the visible pixels, centre that on a
        transparent square, and scale down.
        """
        logo = Image.open(resource_path("logo.png")).convert("RGBA")
        bbox = logo.getchannel("A").getbbox() or logo.getbbox()
        logo = logo.crop(bbox)

        side = max(logo.size)
        canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        canvas.paste(logo, ((side - logo.width) // 2, (side - logo.height) // 2))
        return canvas.resize((size, size), Image.LANCZOS)

    try:
        icon_image = build_tray_image()
    except Exception:
        icon_image = Image.new('RGBA', (64, 64), color=(0, 210, 255, 255))

    def show_window(icon, item):
        # We must call show() in the main thread
        from PySide6.QtCore import QMetaObject, Qt
        QMetaObject.invokeMethod(app, "showNormal", Qt.QueuedConnection)
        QMetaObject.invokeMethod(app, "activateWindow", Qt.QueuedConnection)

    def quit_app(icon, item):
        icon.stop()
        hotkey_manager.shutdown()
        from PySide6.QtCore import QMetaObject, Qt
        QMetaObject.invokeMethod(qt_app, "quit", Qt.QueuedConnection)

    tray_icon = pystray.Icon("SidSoundboard", icon_image, "SidSoundboard", menu=pystray.Menu(
        pystray.MenuItem(i18n.tr("tray.open"), show_window, default=True),
        pystray.MenuItem(i18n.tr("tray.quit"), quit_app)
    ))

    threading.Thread(target=tray_icon.run, daemon=True).start()

    # Hide window instead of closing on X button
    def closeEvent(event):
        event.ignore()
        app.hide()
    app.closeEvent = closeEvent

    app.show()
    sys.exit(qt_app.exec())

if __name__ == "__main__":
    main()
