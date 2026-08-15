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


if __name__ == "__main__":
    unittest.main()
