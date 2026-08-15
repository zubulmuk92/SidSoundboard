import unittest
from unittest.mock import MagicMock, patch

from hotkey_manager import HotkeyManager


class TestShouldRegister(unittest.TestCase):
    def test_true_when_hotkey_and_filename_set(self):
        self.assertTrue(
            HotkeyManager._should_register({"hotkey": "f1", "filename": "x.wav"})
        )

    def test_false_when_hotkey_is_none_sentinel(self):
        self.assertFalse(
            HotkeyManager._should_register({"hotkey": "None", "filename": "x.wav"})
        )

    def test_false_when_no_filename(self):
        self.assertFalse(
            HotkeyManager._should_register({"hotkey": "f1", "filename": None})
        )

    def test_false_when_no_hotkey(self):
        self.assertFalse(
            HotkeyManager._should_register({"hotkey": None, "filename": "x.wav"})
        )


class TestPlaySoundCallback(unittest.TestCase):
    def test_uses_filename_key_and_forwards_sound_id(self):
        audio_manager = MagicMock()
        config = {
            "sounds": [], "primary_output": "Speakers",
            "secondary_output": None, "dual_output_enabled": False,
        }
        manager = HotkeyManager(audio_manager, config)

        sound = {
            "id": "abc123", "name": "Test", "filename": "C:/sounds/test.wav",
            "hotkey": "f1", "volume": 100,
        }
        manager._play_sound_callback(sound)

        audio_manager.toggle_play_pause.assert_called_once()
        _, kwargs = audio_manager.toggle_play_pause.call_args
        self.assertEqual(kwargs["filepath_primary"], "C:/sounds/test.wav")
        self.assertEqual(kwargs["sound_id"], "abc123")

    def test_prefers_the_effects_cache_when_present(self):
        import os
        import tempfile

        tmpdir = tempfile.mkdtemp()
        fx = os.path.join(tmpdir, "abc_fx.wav")
        with open(fx, "wb") as f:
            f.write(b"\x00")

        audio_manager = MagicMock()
        config = {
            "sounds": [], "primary_output": "Speakers",
            "secondary_output": None, "dual_output_enabled": False,
        }
        manager = HotkeyManager(audio_manager, config)
        manager._play_sound_callback({
            "id": "abc", "name": "Test", "filename": "C:/sounds/test.wav",
            "cached_effects_file": fx, "hotkey": "f1", "volume": 100,
        })

        _, kwargs = audio_manager.toggle_play_pause.call_args
        self.assertEqual(kwargs["filepath_primary"], fx)
        self.assertEqual(kwargs["filepath_secondary"], fx)


class TestPanicHotkeyRegistration(unittest.TestCase):
    def test_uses_panic_hotkey_key_and_skips_none_sentinel(self):
        audio_manager = MagicMock()

        with patch("hotkey_manager.keyboard.on_press_key") as mock_on_press_key:
            manager = HotkeyManager(audio_manager, {"panic_hotkey": "f9", "sounds": []})
            manager.load_hotkeys(manager.config)
            mock_on_press_key.assert_called_once()
            self.assertEqual(mock_on_press_key.call_args[0][0], "f9")

        with patch("hotkey_manager.keyboard.on_press_key") as mock_on_press_key:
            manager = HotkeyManager(audio_manager, {"panic_hotkey": "None", "sounds": []})
            manager.load_hotkeys(manager.config)
            mock_on_press_key.assert_not_called()

        with patch("hotkey_manager.keyboard.on_press_key") as mock_on_press_key:
            manager = HotkeyManager(audio_manager, {"sounds": []})
            manager.load_hotkeys(manager.config)
            mock_on_press_key.assert_not_called()


class TestSoloMode(unittest.TestCase):
    SOUND = {"id": "abc", "name": "T", "filename": "x.wav", "hotkey": "f1"}

    def _manager(self, focused_id):
        audio_manager = MagicMock()
        audio_manager.focused_info = (
            {"sound_id": focused_id} if focused_id is not None else None
        )
        config = {
            "sounds": [], "mode_solo": True, "primary_output": "Speakers",
            "secondary_output": None, "dual_output_enabled": False,
        }
        return audio_manager, HotkeyManager(audio_manager, config)

    def test_solo_cuts_a_different_sound(self):
        audio_manager, manager = self._manager("other")
        manager._play_sound_callback(self.SOUND)
        audio_manager.stop_all.assert_called_once()

    def test_solo_does_not_cut_the_sound_being_toggled(self):
        audio_manager, manager = self._manager("abc")
        manager._play_sound_callback(self.SOUND)
        audio_manager.stop_all.assert_not_called()
        audio_manager.toggle_play_pause.assert_called_once()

    def test_solo_with_nothing_playing_cuts_nothing(self):
        audio_manager, manager = self._manager(None)
        manager._play_sound_callback(self.SOUND)
        audio_manager.stop_all.assert_called_once()


if __name__ == "__main__":
    unittest.main()
