import unittest

from ui.views.welcome_view import find_virtual_cable


class TestFindVirtualCable(unittest.TestCase):
    def test_detects_vb_cable(self):
        names = ["Haut-parleurs (Realtek)", "CABLE Input (VB-Audio Virtual Cable)"]
        self.assertEqual(find_virtual_cable(names), names[1])

    def test_detects_voicemeeter(self):
        names = ["Casque", "VoiceMeeter Input (VB-Audio VoiceMeeter VAIO)"]
        self.assertEqual(find_virtual_cable(names), names[1])

    def test_is_case_insensitive(self):
        self.assertIsNotNone(find_virtual_cable(["cable input"]))

    def test_returns_none_without_a_cable(self):
        self.assertIsNone(find_virtual_cable(["Haut-parleurs", "Écouteurs Bluetooth"]))

    def test_survives_an_empty_or_missing_name(self):
        self.assertIsNone(find_virtual_cable([None, ""]))

    def test_returns_the_first_match(self):
        names = ["CABLE Input", "VoiceMeeter Input"]
        self.assertEqual(find_virtual_cable(names), "CABLE Input")


if __name__ == "__main__":
    unittest.main()
