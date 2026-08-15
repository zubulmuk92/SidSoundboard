"""
Scene management from the Settings screen.

The regression these lock down: the scene list was read once at build time,
so a scene created from the sidebar never appeared here, and renaming
silently acted on the wrong entry.
"""

import tempfile
import unittest
from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QApplication, QMessageBox

import config_manager
import paths
import profiles
from ui.views.settings_view import SettingsView

app = QApplication.instance() or QApplication([])


class SceneSettingsCase(unittest.TestCase):
    def setUp(self):
        self._saved = paths._data_dir
        paths.set_data_dir(tempfile.mkdtemp())
        self.config = config_manager.load_config()
        self.changed = []

        audio_manager = MagicMock()
        audio_manager.get_output_devices.return_value = [{"name": "Casque", "id": 1}]
        self.view = SettingsView(
            audio_manager, self.config, lambda c: None, lambda: None,
            on_scenes_changed=lambda: self.changed.append(True),
        )

    def tearDown(self):
        paths.set_data_dir(self._saved)

    def names(self):
        return [p["name"] for p in self.config["profiles"]]

    def combo_names(self):
        return [self.view.cb_scene.itemText(i) for i in range(self.view.cb_scene.count())]


class TestStaleList(SceneSettingsCase):
    def test_a_scene_created_elsewhere_shows_up_after_refresh(self):
        profiles.create_profile(self.config, "Stream")
        self.assertEqual(len(self.combo_names()), 1, "liste encore construite au démarrage")
        self.view.refresh_scenes()
        self.assertEqual(self.combo_names(), ["Général", "Stream"])

    def test_refresh_keeps_the_current_selection(self):
        created = profiles.create_profile(self.config, "Stream")
        self.view.refresh_scenes()
        self.view.cb_scene.setCurrentIndex(1)
        profiles.create_profile(self.config, "Soirée")
        self.view.refresh_scenes()
        self.assertEqual(self.view.cb_scene.currentData(), created["id"])


class TestRename(SceneSettingsCase):
    def test_renaming_the_selected_scene(self):
        profiles.create_profile(self.config, "Stream")
        self.view.refresh_scenes()
        self.view.cb_scene.setCurrentIndex(1)
        with patch("ui.views.settings_view.QInputDialog.getText",
                   return_value=("Soirée", True)):
            self.view._rename_scene()
        self.assertEqual(self.names(), ["Général", "Soirée"])
        self.assertTrue(self.changed)

    def test_cancelling_changes_nothing(self):
        with patch("ui.views.settings_view.QInputDialog.getText",
                   return_value=("Ignoré", False)):
            self.view._rename_scene()
        self.assertEqual(self.names(), ["Général"])
        self.assertFalse(self.changed)

    def test_an_empty_name_changes_nothing(self):
        with patch("ui.views.settings_view.QInputDialog.getText",
                   return_value=("   ", True)):
            self.view._rename_scene()
        self.assertEqual(self.names(), ["Général"])


class TestDelete(SceneSettingsCase):
    def test_deleting_a_confirmed_scene(self):
        profiles.create_profile(self.config, "Stream")
        self.view.refresh_scenes()
        self.view.cb_scene.setCurrentIndex(1)
        with patch("ui.views.settings_view.QMessageBox.question",
                   return_value=QMessageBox.Yes):
            self.view._delete_scene()
        self.assertEqual(self.names(), ["Général"])

    def test_declining_keeps_the_scene(self):
        profiles.create_profile(self.config, "Stream")
        self.view.refresh_scenes()
        self.view.cb_scene.setCurrentIndex(1)
        with patch("ui.views.settings_view.QMessageBox.question",
                   return_value=QMessageBox.No):
            self.view._delete_scene()
        self.assertEqual(self.names(), ["Général", "Stream"])

    def test_the_last_scene_is_protected_with_an_explanation(self):
        with patch("ui.views.settings_view.QMessageBox.information") as info, \
             patch("ui.views.settings_view.QMessageBox.question") as question:
            self.view._delete_scene()
        self.assertTrue(info.called, "l'utilisateur doit savoir pourquoi")
        self.assertFalse(question.called, "ne pas demander de confirmer l'impossible")
        self.assertEqual(self.names(), ["Général"])

    def test_deleting_the_active_scene_moves_the_selection(self):
        created = profiles.create_profile(self.config, "Stream")
        profiles.set_active(self.config, created["id"])
        self.view.refresh_scenes()
        self.view.cb_scene.setCurrentIndex(1)
        with patch("ui.views.settings_view.QMessageBox.question",
                   return_value=QMessageBox.Yes):
            self.view._delete_scene()
        self.assertEqual(self.config["active_profile"], self.config["profiles"][0]["id"])


if __name__ == "__main__":
    unittest.main()
