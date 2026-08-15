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

        panic_hotkey = self.config.get("panic_hotkey")
        if panic_hotkey and panic_hotkey != "None":
            try:
                self.panic_hook = keyboard.on_press_key(panic_hotkey, self._panic_callback)
            except Exception as e:
                print(f"Failed to register panic key: {e}")

        for sound in self.config.get("sounds", []):
            if self._should_register(sound):
                try:
                    hk = keyboard.add_hotkey(sound["hotkey"], self._play_sound_callback, args=(sound,))
                    self.registered_hotkeys.append(hk)
                except Exception as e:
                    print(f"Failed to register hotkey {sound['hotkey']}: {e}")

    @staticmethod
    def _should_register(sound):
        hotkey = sound.get("hotkey")
        filepath = sound.get("filename")
        return bool(hotkey) and hotkey != "None" and bool(filepath)

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
        vol_p = sound.get("volume", 100)
        spd = sound.get("speed", 100)
        global_sec_vol = self.config.get("global_secondary_volume", 100)
        vol_s = int(vol_p * (global_sec_vol / 100.0))

        original_file = sound.get("filename")
        from audio_processor import generate_cached_file_sync
        try:
            filepath_sec = generate_cached_file_sync(original_file, vol_s, spd)
        except Exception:
            filepath_sec = original_file

        if self.config.get("mode_solo", False):
            self.audio_manager.stop_all()

        self.audio_manager.toggle_play_pause(
            filepath_primary=sound.get("cached_file_primary") or sound.get("cached_file") or original_file,
            filepath_secondary=filepath_sec,
            name=sound.get("name", "Unknown"),
            volume=1.0,
            primary_device_name=self.config.get("primary_output"),
            secondary_device_name=self.config.get("secondary_output"),
            dual_enabled=self.config.get("dual_output_enabled", False),
            sound_id=sound.get("id")
        )

    def _panic_callback(self, event):
        self.audio_manager.stop_all()

    def shutdown(self):
        self._clear_hotkeys()
