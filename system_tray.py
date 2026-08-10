import pystray
from PIL import Image
import webbrowser
import threading
import sys
import os

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class SystemTray:
    def __init__(self, app, on_show, on_quit):
        self.app = app
        self.on_show = on_show
        self.on_quit = on_quit
        self.icon = None

    def create_tray(self):
        try:
            image = Image.open(resource_path("logo_sq.png"))
        except Exception:
            image = Image.new('RGB', (64, 64), color=(0, 0, 0))
            
        menu = pystray.Menu(
            pystray.MenuItem("Ouvrir l'Interface", self.open_ui, default=True),
            pystray.MenuItem("Quitter", self.quit_app)
        )
        
        self.icon = pystray.Icon("sidsoundboard", image, "SidSoundboard v11", menu)
        self.icon.run()

    def open_ui(self, icon, item):
        webbrowser.open("http://127.0.0.1:5000")

    def quit_app(self, icon, item):
        self.icon.stop()
        self.on_quit()
