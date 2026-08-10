import sys
import os
from config_manager import load_config
from audio_manager import AudioManager
from hotkey_manager import HotkeyManager
from gui import AppGUI

def main():
    if sys.stdout is None:
        sys.stdout = open(os.devnull, 'w')
    if sys.stderr is None:
        sys.stderr = open(os.devnull, 'w')
        
    config = load_config()
    
    audio_manager = AudioManager()
    
    hotkey_manager = HotkeyManager(audio_manager, config)
    hotkey_manager.load_hotkeys(config)
    
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
        app.after(0, app.deiconify)
        
    def quit_app(icon, item):
        icon.stop()
        hotkey_manager.shutdown()
        app.after(0, app.destroy)
        
    tray_icon = pystray.Icon("SidSoundboard", icon_image, "SidSoundboard v12", menu=pystray.Menu(
        pystray.MenuItem("Ouvrir l'Interface", show_window, default=True),
        pystray.MenuItem("Quitter", quit_app)
    ))
    
    threading.Thread(target=tray_icon.run, daemon=True).start()
    
    def on_closing():
        # Cacher la fenêtre au lieu de la fermer
        app.withdraw()
        
    app.protocol("WM_DELETE_WINDOW", on_closing)
    app.mainloop()

if __name__ == "__main__":
    main()
