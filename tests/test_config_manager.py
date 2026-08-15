import unittest

import config_manager


class TestMigrateSounds(unittest.TestCase):
    def test_backfills_every_effect_default(self):
        config = {"sounds": [{"id": "a", "filename": "a.wav"}]}
        config_manager.migrate_sounds(config)
        sound = config["sounds"][0]
        self.assertEqual(sound["volume"], 100)
        self.assertEqual(sound["speed"], 100)
        self.assertEqual(sound["bass_boost"], 0)
        self.assertEqual(sound["reverb"], 0)
        self.assertEqual(sound["trim_start_sec"], 0.0)
        self.assertIsNone(sound["trim_end_sec"])
        self.assertIsNone(sound["cached_effects_file"])

    def test_preserves_existing_values(self):
        config = {"sounds": [{"id": "a", "volume": 250, "bass_boost": 40}]}
        config_manager.migrate_sounds(config)
        self.assertEqual(config["sounds"][0]["volume"], 250)
        self.assertEqual(config["sounds"][0]["bass_boost"], 40)

    def test_per_sound_fades_inherit_the_global_values(self):
        config = {"fade_in_ms": 300, "fade_out_ms": 400, "sounds": [{"id": "a"}]}
        config_manager.migrate_sounds(config)
        self.assertEqual(config["sounds"][0]["fade_in_ms"], 300)
        self.assertEqual(config["sounds"][0]["fade_out_ms"], 400)

    def test_handles_a_config_with_no_sounds(self):
        config = {}
        self.assertIs(config_manager.migrate_sounds(config), config)


class TestMigrateSettings(unittest.TestCase):
    def test_carries_the_old_ducking_choice_to_a_volume(self):
        config = {"audio_ducking_level": "Fort (80%)"}
        config_manager.migrate_settings(config)
        self.assertEqual(config["global_secondary_volume"], 20)
        self.assertNotIn("audio_ducking_level", config)

    def test_maps_every_legacy_choice(self):
        expected = {"Aucun": 100, "Léger (50%)": 50, "Fort (80%)": 20, "Total (100%)": 0}
        for legacy, volume in expected.items():
            config = {"audio_ducking_level": legacy}
            config_manager.migrate_settings(config)
            self.assertEqual(config["global_secondary_volume"], volume, legacy)

    def test_an_explicit_volume_wins_over_the_legacy_key(self):
        config = {"audio_ducking_level": "Fort (80%)", "global_secondary_volume": 75}
        config_manager.migrate_settings(config)
        self.assertEqual(config["global_secondary_volume"], 75)

    def test_leaves_a_config_without_the_legacy_key_alone(self):
        config = {}
        config_manager.migrate_settings(config)
        self.assertNotIn("global_secondary_volume", config)


if __name__ == "__main__":
    unittest.main()
