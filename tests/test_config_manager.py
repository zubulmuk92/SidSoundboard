import json
import os
import tempfile
import unittest

import config_manager
import paths
import profiles


class MigrationCase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self._saved_dir = paths._data_dir
        paths.set_data_dir(self.tmpdir)

    def tearDown(self):
        paths.set_data_dir(self._saved_dir)


class TestMigrateV1ToV2(MigrationCase):
    def test_a_flat_library_becomes_one_profile(self):
        config = config_manager.migrate({"sounds": [{"id": "a", "filename": "x.wav"}]},
                                        self.tmpdir)
        self.assertEqual(len(config["profiles"]), 1)
        self.assertEqual(len(profiles.active_sounds(config)), 1)
        self.assertNotIn("sounds", config)

    def test_the_version_is_stamped(self):
        config = config_manager.migrate({}, self.tmpdir)
        self.assertEqual(config["config_version"], config_manager.CONFIG_VERSION)

    def test_a_current_config_is_left_alone(self):
        config = config_manager.migrate({"sounds": [{"id": "a"}]}, self.tmpdir)
        name_before = config["profiles"][0]["id"]
        again = config_manager.migrate(config, self.tmpdir)
        self.assertEqual(len(again["profiles"]), 1)
        self.assertEqual(again["profiles"][0]["id"], name_before)

    def test_the_legacy_ducking_choice_is_carried_over(self):
        config = config_manager.migrate({"audio_ducking_level": "Fort (80%)"}, self.tmpdir)
        self.assertEqual(config["global_secondary_volume"], 20)
        self.assertNotIn("audio_ducking_level", config)

    def test_the_dead_main_volume_key_is_dropped(self):
        config = config_manager.migrate({"main_volume": 1.0}, self.tmpdir)
        self.assertNotIn("main_volume", config)

    def test_effect_defaults_are_backfilled(self):
        config = config_manager.migrate({"sounds": [{"id": "a"}]}, self.tmpdir)
        sound = profiles.active_sounds(config)[0]
        self.assertEqual(sound["volume"], 100)
        self.assertIsNone(sound["trim_end_sec"])

    def test_per_sound_fades_inherit_the_global_values(self):
        config = config_manager.migrate(
            {"fade_in_ms": 300, "fade_out_ms": 400, "sounds": [{"id": "a"}]}, self.tmpdir
        )
        sound = profiles.active_sounds(config)[0]
        self.assertEqual(sound["fade_in_ms"], 300)
        self.assertEqual(sound["fade_out_ms"], 400)

    def test_existing_values_survive(self):
        config = config_manager.migrate(
            {"sounds": [{"id": "a", "volume": 250, "bass_boost": 40}]}, self.tmpdir
        )
        sound = profiles.active_sounds(config)[0]
        self.assertEqual(sound["volume"], 250)
        self.assertEqual(sound["bass_boost"], 40)


class TestAbsolutizePaths(MigrationCase):
    def test_relative_paths_resolve_against_the_config_folder(self):
        config = config_manager.migrate(
            {"sounds": [{"id": "a", "filename": os.path.join("downloads", "x.wav")}]},
            self.tmpdir,
        )
        filename = profiles.active_sounds(config)[0]["filename"]
        self.assertTrue(os.path.isabs(filename))
        self.assertEqual(
            filename, os.path.join(self.tmpdir, "downloads", "x.wav")
        )

    def test_absolute_paths_are_untouched(self):
        absolute = os.path.join(self.tmpdir, "elsewhere", "y.wav")
        config = config_manager.migrate(
            {"sounds": [{"id": "a", "filename": absolute}]}, self.tmpdir
        )
        self.assertEqual(profiles.active_sounds(config)[0]["filename"], absolute)

    def test_every_path_key_is_covered(self):
        config = config_manager.migrate({"sounds": [{
            "id": "a", "filename": "a.wav",
            "cached_effects_file": "a_fx.wav", "cached_secondary_file": "a_sec.wav",
        }]}, self.tmpdir)
        sound = profiles.active_sounds(config)[0]
        for key in ("filename", "cached_effects_file", "cached_secondary_file"):
            self.assertTrue(os.path.isabs(sound[key]), key)


class TestLoadAndSave(MigrationCase):
    def test_a_missing_config_yields_usable_defaults(self):
        config = config_manager.load_config()
        self.assertEqual(config["config_version"], config_manager.CONFIG_VERSION)
        self.assertEqual(len(config["profiles"]), 1)

    def test_defaults_are_not_shared_between_loads(self):
        first = config_manager.load_config()
        profiles.active_sounds(first).append({"id": "a"})
        second = config_manager.load_config()
        self.assertEqual(profiles.active_sounds(second), [])

    def test_a_saved_config_round_trips(self):
        config = config_manager.load_config()
        profiles.active_sounds(config).append({"id": "a", "name": "Test"})
        config_manager.save_config(config)
        reloaded = config_manager.load_config()
        self.assertEqual(profiles.active_sounds(reloaded)[0]["name"], "Test")

    def test_a_corrupt_config_falls_back_instead_of_crashing(self):
        with open(paths.config_path(), "w", encoding="utf-8") as f:
            f.write("{ not json")
        config = config_manager.load_config()
        self.assertEqual(len(config["profiles"]), 1)


class TestLegacyPickup(unittest.TestCase):
    """The upgrade path: a config left in the old working-directory
    location must be adopted, with its relative sound paths resolved
    against that old location rather than lost."""

    def setUp(self):
        self.old_cwd = os.getcwd()
        self.legacy_dir = tempfile.mkdtemp()
        self.data = tempfile.mkdtemp()
        self._saved_dir = paths._data_dir
        paths.set_data_dir(self.data)
        os.chdir(self.legacy_dir)
        with open(os.path.join(self.legacy_dir, "config.json"), "w", encoding="utf-8") as f:
            json.dump({"sounds": [{"id": "a", "name": "Vieux",
                                   "filename": os.path.join("downloads", "old.wav")}]}, f)

    def tearDown(self):
        os.chdir(self.old_cwd)
        paths.set_data_dir(self._saved_dir)

    def test_the_legacy_library_is_adopted(self):
        config = config_manager.load_config()
        sounds = profiles.active_sounds(config)
        self.assertEqual(len(sounds), 1)
        self.assertEqual(sounds[0]["name"], "Vieux")

    def test_its_paths_point_at_the_old_folder(self):
        config = config_manager.load_config()
        self.assertEqual(
            profiles.active_sounds(config)[0]["filename"],
            os.path.join(self.legacy_dir, "downloads", "old.wav"),
        )

    def test_it_is_written_to_the_new_location(self):
        config_manager.load_config()
        self.assertTrue(os.path.exists(paths.config_path()))

    def test_the_legacy_file_is_left_in_place(self):
        config_manager.load_config()
        self.assertTrue(os.path.exists(os.path.join(self.legacy_dir, "config.json")))


if __name__ == "__main__":
    unittest.main()
