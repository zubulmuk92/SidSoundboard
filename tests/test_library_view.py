"""
Headless tests for LibraryView's logic — filtering, reordering and
persistence. The rendering needs a screen; none of this does.
"""

import tempfile
import unittest
from unittest.mock import MagicMock

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QApplication

import config_manager
import paths
import profiles
from ui.views.library_view import LibraryView

app = QApplication.instance() or QApplication([])


def sound(sound_id, name, color="Gris", hotkey="None"):
    return {"id": sound_id, "name": name, "filename": "x.wav",
            "hotkey": hotkey, "color": color, "volume": 100}


class LibraryCase(unittest.TestCase):
    def setUp(self):
        self._saved = paths._data_dir
        paths.set_data_dir(tempfile.mkdtemp())
        self.config = config_manager.load_config()
        profiles.active_sounds(self.config).extend([
            sound("a", "Alpha", "Musiques", "f1"),
            sound("b", "Bravo", "SFX", "f2"),
            sound("c", "Charlie", "Musiques", "f1"),
        ])
        self.view = LibraryView(self.config, MagicMock())

    def tearDown(self):
        paths.set_data_dir(self._saved)

    def ids(self):
        return [s["id"] for s in self.view.filtered_sounds]


class TestFiltering(LibraryCase):
    def test_everything_is_shown_by_default(self):
        self.assertEqual(self.ids(), ["a", "b", "c"])

    def test_search_matches_the_name(self):
        self.view.search_input.setText("bra")
        self.view._filter_sounds()
        self.assertEqual(self.ids(), ["b"])

    def test_search_matches_the_hotkey(self):
        self.view.search_input.setText("f2")
        self.view._filter_sounds()
        self.assertEqual(self.ids(), ["b"])

    def test_a_category_chip_narrows_the_grid(self):
        self.view._set_category_filter("Musiques")
        self.assertEqual(self.ids(), ["a", "c"])

    def test_clicking_the_same_chip_again_clears_it(self):
        self.view._set_category_filter("Musiques")
        self.view._set_category_filter("Musiques")
        self.assertEqual(self.ids(), ["a", "b", "c"])

    def test_category_and_search_combine(self):
        self.view._set_category_filter("Musiques")
        self.view.search_input.setText("alpha")
        self.view._filter_sounds()
        self.assertEqual(self.ids(), ["a"])

    def test_only_used_categories_get_a_chip(self):
        # Three sounds spanning two categories: "All" + 2 chips + a stretch.
        self.assertEqual(self.view.filter_row.count(), 4)

    def test_no_chips_at_all_when_the_profile_is_empty(self):
        self.view.sounds.clear()
        self.view._filter_sounds()
        self.assertEqual(self.view.filter_row.count(), 0)


class TestReordering(LibraryCase):
    def order(self):
        return [s["id"] for s in profiles.active_sounds(self.config)]

    def test_moving_onto_a_later_sound_takes_its_place(self):
        self.assertTrue(self.view.move_sound("a", "c"))
        self.assertEqual(self.order(), ["b", "a", "c"])

    def test_moving_onto_an_earlier_sound_moves_it_up(self):
        self.assertTrue(self.view.move_sound("c", "a"))
        self.assertEqual(self.order(), ["c", "a", "b"])

    def test_moving_onto_itself_changes_nothing(self):
        self.assertFalse(self.view.move_sound("b", "b"))
        self.assertEqual(self.order(), ["a", "b", "c"])

    def test_an_unknown_target_changes_nothing(self):
        self.assertFalse(self.view.move_sound("a", None))
        self.assertFalse(self.view.move_sound("a", "ghost"))
        self.assertEqual(self.order(), ["a", "b", "c"])

    def test_an_unknown_source_changes_nothing(self):
        self.assertFalse(self.view.move_sound("ghost", "a"))
        self.assertEqual(self.order(), ["a", "b", "c"])

    def test_the_new_order_is_persisted(self):
        self.view.move_sound("a", "c")
        reloaded = config_manager.load_config()
        self.assertEqual([s["id"] for s in profiles.active_sounds(reloaded)],
                         ["b", "a", "c"])

    def test_a_drop_lands_on_the_card_under_the_cursor(self):
        # The only test that needs a real layout pass, so geometry is set.
        self.view.resize(1200, 600)
        self.view.show()
        app.processEvents()
        self.view._on_card_dropped("a", self.view.cards["c"].geometry().center())
        self.view.hide()
        self.assertEqual(self.order(), ["b", "a", "c"])

    def test_a_drop_on_empty_space_changes_nothing(self):
        self.view._on_card_dropped("a", QPoint(9999, 9999))
        self.assertEqual(self.order(), ["a", "b", "c"])


class TestPersistence(LibraryCase):
    def test_a_volume_change_is_written_to_the_active_profile(self):
        self.view._on_volume_changed("a", 250)
        reloaded = config_manager.load_config()
        first = profiles.active_sounds(reloaded)[0]
        self.assertEqual(first["volume"], 250)

    def test_a_category_change_is_written(self):
        self.view._on_color_changed("a", "Voix")
        reloaded = config_manager.load_config()
        self.assertEqual(profiles.active_sounds(reloaded)[0]["color"], "Voix")

    def test_sounds_land_in_the_active_profile_only(self):
        other = profiles.create_profile(self.config, "Autre")
        self.assertEqual(other["sounds"], [])
        self.assertEqual(len(profiles.active_sounds(self.config)), 3)


if __name__ == "__main__":
    unittest.main()
