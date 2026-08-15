import unittest

import profiles


class TestEnsureProfiles(unittest.TestCase):
    def test_wraps_a_flat_sound_list_into_one_profile(self):
        config = {"sounds": [{"id": "a"}, {"id": "b"}]}
        profiles.ensure_profiles(config)
        self.assertEqual(len(config["profiles"]), 1)
        self.assertEqual(config["profiles"][0]["name"], profiles.DEFAULT_PROFILE_NAME)
        self.assertEqual([s["id"] for s in config["profiles"][0]["sounds"]], ["a", "b"])
        self.assertNotIn("sounds", config)

    def test_creates_an_empty_profile_for_an_empty_config(self):
        config = {}
        profiles.ensure_profiles(config)
        self.assertEqual(len(config["profiles"]), 1)
        self.assertEqual(config["profiles"][0]["sounds"], [])

    def test_repairs_an_active_id_that_points_nowhere(self):
        config = {"profiles": [{"id": "x", "name": "X", "sounds": []}],
                  "active_profile": "ghost"}
        profiles.ensure_profiles(config)
        self.assertEqual(config["active_profile"], "x")

    def test_is_idempotent(self):
        config = {"sounds": [{"id": "a"}]}
        profiles.ensure_profiles(config)
        first = config["profiles"][0]["id"]
        profiles.ensure_profiles(config)
        self.assertEqual(len(config["profiles"]), 1)
        self.assertEqual(config["profiles"][0]["id"], first)


class TestAccess(unittest.TestCase):
    def setUp(self):
        self.config = {"profiles": [
            {"id": "p1", "name": "Jeu", "sounds": [{"id": "a"}]},
            {"id": "p2", "name": "Stream", "sounds": [{"id": "b"}, {"id": "c"}]},
        ], "active_profile": "p2"}

    def test_active_sounds_returns_the_active_profile_list(self):
        self.assertEqual([s["id"] for s in profiles.active_sounds(self.config)], ["b", "c"])

    def test_active_sounds_is_the_live_list(self):
        profiles.active_sounds(self.config).append({"id": "d"})
        self.assertEqual(len(self.config["profiles"][1]["sounds"]), 3)

    def test_all_sounds_spans_every_profile(self):
        self.assertEqual(
            sorted(s["id"] for s in profiles.all_sounds(self.config)), ["a", "b", "c"]
        )

    def test_set_active_ignores_an_unknown_id(self):
        profiles.set_active(self.config, "nope")
        self.assertEqual(self.config["active_profile"], "p2")

    def test_set_active_switches(self):
        profiles.set_active(self.config, "p1")
        self.assertEqual([s["id"] for s in profiles.active_sounds(self.config)], ["a"])


class TestMutation(unittest.TestCase):
    def setUp(self):
        self.config = {}
        profiles.ensure_profiles(self.config)
        self.first = self.config["profiles"][0]["id"]

    def test_create_adds_an_empty_profile(self):
        created = profiles.create_profile(self.config, "Soirée")
        self.assertEqual(created["sounds"], [])
        self.assertEqual(len(self.config["profiles"]), 2)

    def test_rename(self):
        profiles.rename_profile(self.config, self.first, "Renommé")
        self.assertEqual(self.config["profiles"][0]["name"], "Renommé")

    def test_rename_ignores_an_empty_name(self):
        before = self.config["profiles"][0]["name"]
        profiles.rename_profile(self.config, self.first, "")
        self.assertEqual(self.config["profiles"][0]["name"], before)

    def test_delete_refuses_the_last_profile(self):
        self.assertFalse(profiles.delete_profile(self.config, self.first))
        self.assertEqual(len(self.config["profiles"]), 1)

    def test_delete_moves_the_active_profile_when_it_was_removed(self):
        second = profiles.create_profile(self.config, "Deux")
        profiles.set_active(self.config, second["id"])
        self.assertTrue(profiles.delete_profile(self.config, second["id"]))
        self.assertEqual(self.config["active_profile"], self.first)

    def test_delete_ignores_an_unknown_id(self):
        profiles.create_profile(self.config, "Deux")
        self.assertFalse(profiles.delete_profile(self.config, "ghost"))
        self.assertEqual(len(self.config["profiles"]), 2)


if __name__ == "__main__":
    unittest.main()
