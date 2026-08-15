import os
import tempfile
import unittest

import cache_manager


class TestCleanupCaches(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def _touch(self, name):
        path = os.path.join(self.tmpdir, name)
        with open(path, "wb") as f:
            f.write(b"\x00")
        return path

    def test_protects_the_original_and_the_effects_cache(self):
        original = self._touch("song_v2_s3.wav")
        effects = self._touch("abc_fx.wav")
        cache_manager.cleanup_caches({
            "sounds": [{"filename": original, "cached_effects_file": effects}]
        })
        self.assertTrue(os.path.exists(original))
        self.assertTrue(os.path.exists(effects))

    def test_protects_the_peaks_of_the_effects_cache(self):
        effects = self._touch("abc_fx.wav")
        peaks = self._touch("abc_fx.wav.peaks.json")
        cache_manager.cleanup_caches({
            "sounds": [{"filename": effects, "cached_effects_file": effects}]
        })
        self.assertTrue(os.path.exists(peaks))

    def test_removes_orphan_ducking_and_effects_files(self):
        keeper = self._touch("kept_fx.wav")
        orphan_ducking = self._touch("kept_fx_v50_s100.wav")
        orphan_effects = self._touch("deleted_fx.wav")
        cache_manager.cleanup_caches({
            "sounds": [{"filename": keeper, "cached_effects_file": keeper}]
        })
        self.assertTrue(os.path.exists(keeper))
        self.assertFalse(os.path.exists(orphan_ducking))
        self.assertFalse(os.path.exists(orphan_effects))

    def test_protects_the_secondary_cache_and_drops_orphan_ones(self):
        keeper = self._touch("kept_fx.wav")
        secondary = self._touch("kept_sec.wav")
        orphan = self._touch("deleted_sec.wav")
        cache_manager.cleanup_caches({
            "sounds": [{
                "filename": keeper, "cached_effects_file": keeper,
                "cached_secondary_file": secondary,
            }]
        })
        self.assertTrue(os.path.exists(secondary))
        self.assertFalse(os.path.exists(orphan))

    def test_always_removes_preview_renders(self):
        keeper = self._touch("kept_fx.wav")
        preview = self._touch("kept_preview.wav")
        cache_manager.cleanup_caches({
            "sounds": [{"filename": keeper, "cached_effects_file": keeper}]
        })
        self.assertFalse(os.path.exists(preview))

    def test_leaves_unrelated_files_alone(self):
        keeper = self._touch("kept_fx.wav")
        unrelated = self._touch("my_music.wav")
        cache_manager.cleanup_caches({
            "sounds": [{"filename": keeper, "cached_effects_file": keeper}]
        })
        self.assertTrue(os.path.exists(unrelated))


if __name__ == "__main__":
    unittest.main()
