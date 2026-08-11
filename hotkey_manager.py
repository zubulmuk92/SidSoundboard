import keyboard

class HotkeyManager:
    def __init__(self, audio_manager, config):
        self.audio_manager = audio_manager
        self.config = config
        self.registered_hotkeys = []
        self.panic_hook = None

    def load_hotkeys(self, config):
        self.config = config
        self._clear_hotkeys()
        
        # Enregistrer la touche panique
        if self.config.get("panic_key"):
            try:
                self.panic_hook = keyboard.on_press_key(self.config["panic_key"], self._panic_callback)
            except Exception as e:
                print(f"Failed to register panic key: {e}")

        # Enregistrer les sons
        for sound in self.config.get("sounds", []):
            hotkey = sound.get("hotkey")
            filepath = sound.get("file")
            if hotkey and filepath:
                try:
                    hk = keyboard.add_hotkey(hotkey, self._play_sound_callback, args=(sound,))
                    self.registered_hotkeys.append(hk)
                except Exception as e:
                    print(f"Failed to register hotkey {hotkey}: {e}")

    def _clear_hotkeys(self):
        for hk in self.registered_hotkeys:
            try:
                keyboard.remove_hotkey(hk)
            except Exception:
                pass
        self.registered_hotkeys.clear()
        
        if self.panic_hook:
            try:
                keyboard.unhook(self.panic_hook)
            except Exception:
                pass
            self.panic_hook = None

    def _play_sound_callback(self, sound):
        self.audio_manager.stop_all()
            
        self.audio_manager.play_sound(
            filepath=sound.get("cached_file") or sound.get("file"),
            name=sound.get("name", "Unknown"),
            volume=1.0, # Volume is baked into the file now
            primary_device_name=self.config.get("primary_output"),
            secondary_device_name=self.config.get("secondary_output"),
            dual_enabled=self.config.get("dual_output_enabled", False)
        )

    def _panic_callback(self, event):
        self.audio_manager.stop_all()

    def shutdown(self):
        self._clear_hotkeys()
