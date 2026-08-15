import json
import os
import tempfile
import unittest
import wave

import audio_processor


class TestGeneratePeaks(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.wav_path = os.path.join(self.tmpdir, "tone.wav")
        with wave.open(self.wav_path, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(44100)
            silence = b"\x00\x00" * 22050
            loud = (30000).to_bytes(2, "little", signed=True) * 22050
            w.writeframes(silence + loud)

    def test_peaks_length_matches_bucket_count(self):
        peaks = audio_processor.generate_peaks(self.wav_path, num_buckets=50)
        self.assertEqual(len(peaks), 50)

    def test_peaks_values_are_normalized(self):
        peaks = audio_processor.generate_peaks(self.wav_path, num_buckets=50)
        self.assertTrue(all(0.0 <= p <= 1.0 for p in peaks))

    def test_second_half_is_louder_than_first(self):
        peaks = audio_processor.generate_peaks(self.wav_path, num_buckets=50)
        first_half_avg = sum(peaks[:25]) / 25
        second_half_avg = sum(peaks[25:]) / 25
        self.assertGreater(second_half_avg, first_half_avg)

    def test_generate_and_save_peaks_writes_json_file(self):
        peaks_path = audio_processor.generate_and_save_peaks(self.wav_path, num_buckets=20)
        self.assertEqual(peaks_path, self.wav_path + ".peaks.json")
        self.assertTrue(os.path.exists(peaks_path))
        with open(peaks_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(len(data["peaks"]), 20)


if __name__ == "__main__":
    unittest.main()
