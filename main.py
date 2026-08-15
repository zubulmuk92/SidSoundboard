import sys
import os
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

from config_manager import load_config
from audio_manager import AudioManager
from hotkey_manager import HotkeyManager
from gui_pyside import AppGUI
import cache_manager

def main():
    if sys.stdout is None:
        sys.stdout = open(os.devnull, 'w')
    if sys.stderr is None:
        sys.stderr = open(os.devnull, 'w')
        
    cache_manager.cleanup_caches()
    
    config = load_config()
    
    audio_manager = AudioManager()
    
    hotkey_manager = HotkeyManager(audio_manager, config)
    hotkey_manager.load_hotkeys(config)
    
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QIcon

    qt_app = QApplication.instance()
    if not qt_app:
        qt_app = QApplication(sys.argv)

    app = AppGUI(audio_manager, hotkey_manager)
    
    # Configuration du System Tray
    import pystray
    from PIL import Image
    import threading
    
    def resource_path(relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)
    
    try:
        icon_image = Image.open(resource_path("logo_sq.png"))
    except:
        icon_image = Image.new('RGB', (64, 64), color=(0, 210, 255))
        
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
        pystray.MenuItem("Ouvrir l'Interface", show_window, default=True),
        pystray.MenuItem("Quitter", quit_app)
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
