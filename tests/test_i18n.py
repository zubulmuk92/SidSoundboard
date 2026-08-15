import unittest

import i18n


class TestTranslation(unittest.TestCase):
    def tearDown(self):
        i18n.set_language(i18n.DEFAULT_LANGUAGE)

    def test_french_is_the_default(self):
        self.assertEqual(i18n.get_language(), "fr")
        self.assertEqual(i18n.tr("panic.button"), "PANIQUE")

    def test_switching_language_changes_the_lookup(self):
        i18n.set_language("en")
        self.assertEqual(i18n.tr("panic.button"), "PANIC")

    def test_an_unknown_code_is_ignored(self):
        i18n.set_language("de")
        self.assertEqual(i18n.get_language(), "fr")

    def test_an_unknown_key_degrades_to_itself(self):
        self.assertEqual(i18n.tr("nope.missing"), "nope.missing")

    def test_placeholders_are_filled(self):
        self.assertEqual(i18n.tr("panic.hint", key="F8"), "ou la touche F8")

    def test_a_missing_placeholder_returns_the_raw_text(self):
        self.assertIn("{key}", i18n.tr("panic.hint", wrong="F8"))

    def test_both_catalogs_cover_the_same_keys(self):
        fr = set(i18n.TRANSLATIONS["fr"])
        en = set(i18n.TRANSLATIONS["en"])
        self.assertEqual(fr - en, set(), "clés manquantes en anglais")
        self.assertEqual(en - fr, set(), "clés en trop en anglais")


class TestCategories(unittest.TestCase):
    def tearDown(self):
        i18n.set_language(i18n.DEFAULT_LANGUAGE)

    def test_category_labels_translate(self):
        self.assertEqual(i18n.category_label("Musiques"), "Musiques")
        i18n.set_language("en")
        self.assertEqual(i18n.category_label("Musiques"), "Music")

    def test_labels_round_trip_back_to_the_stored_key(self):
        for language in ("fr", "en"):
            i18n.set_language(language)
            for key in ("Sons Troll", "Musiques", "SFX", "Voix", "Ambiance", "Gris"):
                self.assertEqual(
                    i18n.category_key(i18n.category_label(key)), key, f"{language}/{key}"
                )

    def test_an_unknown_label_passes_through(self):
        self.assertEqual(i18n.category_key("Perso"), "Perso")


if __name__ == "__main__":
    unittest.main()
