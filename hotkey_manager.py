import keyboard

import profiles

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

        # Only the active profile is bound: the same key can serve a
        # different sound in another profile, which is the point.
        for sound in profiles.active_sounds(self.config):
            if self._should_register(sound):
                try:
                    hk = keyboard.add_hotkey(sound["hotkey"], self._play_sound_callback, args=(sound,))
                    self.registered_hotkeys.append(hk)
                except Exception as e:
                    print(f"Failed to register hotkey {sound['hotkey']}: {e}")

    @staticmethod
    def find_conflicts(sounds):
        """
        Maps each hotkey claimed by more than one sound to those sounds.
        Two sounds could always bind the same key, with the last one
        registered silently winning; this is what lets the UI say so.
        """
        claimed = {}
        for sound in sounds:
            hotkey = sound.get("hotkey")
            if hotkey and hotkey != "None":
                claimed.setdefault(hotkey, []).append(sound)
        return {k: v for k, v in claimed.items() if len(v) > 1}

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
        from audio_processor import resolve_playback_file, resolve_secondary_file

        playback_file = resolve_playback_file(sound)
        if not playback_file:
            return

        # Effects are baked into playback_file; the secondary route is a
        # pre-rendered attenuated copy of it. Nothing is computed here — a
        # hotkey must fire instantly.
        filepath_sec = resolve_secondary_file(sound)

        # Solo cuts everything else — but never the sound being toggled,
        # or pausing it would drop its position and restart from zero.
        focused = self.audio_manager.focused_info
        same_sound = focused and focused.get("sound_id") == sound.get("id")
        if self.config.get("mode_solo", False) and not same_sound:
            self.audio_manager.stop_all()

        self.audio_manager.set_fade_durations(
            sound.get("fade_in_ms", self.config.get("fade_in_ms", 150)),
            sound.get("fade_out_ms", self.config.get("fade_out_ms", 150)),
        )

        self.audio_manager.toggle_play_pause(
            filepath_primary=playback_file,
            filepath_secondary=filepath_sec,
            name=sound.get("name", "Unknown"),
            volume=1.0,
            primary_device_name=self.config.get("primary_output"),
            secondary_device_name=self.config.get("secondary_output"),
            dual_enabled=self.config.get("dual_output_enabled", False),
            sound_id=sound.get("id"),
            loop=sound.get("loop", False)
        )

    def _panic_callback(self, event):
        self.audio_manager.stop_all()

    def shutdown(self):
        self._clear_hotkeys()
