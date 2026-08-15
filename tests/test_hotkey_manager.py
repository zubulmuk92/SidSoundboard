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


if __name__ == "__main__":
    unittest.main()
