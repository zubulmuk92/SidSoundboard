import os
import tempfile
import unittest
from unittest.mock import patch

import paths


class TestDataDir(unittest.TestCase):
    def setUp(self):
        self._saved = paths._data_dir
        paths.set_data_dir(None)

    def tearDown(self):
        paths.set_data_dir(self._saved)

    def test_uses_the_app_folder_when_it_is_writable(self):
        writable = tempfile.mkdtemp()
        with patch.object(paths, "app_dir", return_value=writable):
            self.assertEqual(paths.data_dir(), writable)

    def test_falls_back_to_appdata_when_it_is_not(self):
        fallback = tempfile.mkdtemp()
        with patch.object(paths, "app_dir", return_value="Z:\\nope"), \
             patch.dict(os.environ, {"APPDATA": fallback}):
            self.assertEqual(paths.data_dir(), os.path.join(fallback, paths.APP_NAME))

    def test_the_fallback_folder_is_created(self):
        fallback = tempfile.mkdtemp()
        with patch.object(paths, "app_dir", return_value="Z:\\nope"), \
             patch.dict(os.environ, {"APPDATA": fallback}):
            self.assertTrue(os.path.isdir(paths.data_dir()))

    def test_it_is_resolved_only_once(self):
        first = tempfile.mkdtemp()
        with patch.object(paths, "app_dir", return_value=first):
            paths.data_dir()
        with patch.object(paths, "app_dir", return_value=tempfile.mkdtemp()):
            self.assertEqual(paths.data_dir(), first)


class TestWritableProbe(unittest.TestCase):
    def test_a_real_write_decides(self):
        self.assertTrue(paths._is_writable(tempfile.mkdtemp()))

    def test_an_impossible_location_is_rejected(self):
        self.assertFalse(paths._is_writable("Z:\\definitely\\not\\here"))

    def test_the_probe_file_is_cleaned_up(self):
        directory = tempfile.mkdtemp()
        paths._is_writable(directory)
        self.assertEqual(os.listdir(directory), [])


class TestDerivedPaths(unittest.TestCase):
    def setUp(self):
        self._saved = paths._data_dir
        self.tmpdir = tempfile.mkdtemp()
        paths.set_data_dir(self.tmpdir)

    def tearDown(self):
        paths.set_data_dir(self._saved)

    def test_config_sits_in_the_data_folder(self):
        self.assertEqual(paths.config_path(), os.path.join(self.tmpdir, "config.json"))

    def test_downloads_is_created_on_demand(self):
        directory = paths.downloads_dir()
        self.assertTrue(os.path.isdir(directory))
        self.assertEqual(directory, os.path.join(self.tmpdir, "downloads"))

    def test_logs_sit_in_the_data_folder(self):
        self.assertEqual(paths.log_path("errors.log"),
                         os.path.join(self.tmpdir, "errors.log"))


if __name__ == "__main__":
    unittest.main()
