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


class TestBuildEffectsFilterChain(unittest.TestCase):
    def test_empty_when_all_effects_neutral(self):
        chain = audio_processor.build_effects_filter_chain(
            {"volume": 100, "speed": 100, "bass_boost": 0, "reverb": 0}
        )
        self.assertEqual(chain, "")

    def test_missing_keys_are_treated_as_neutral(self):
        self.assertEqual(audio_processor.build_effects_filter_chain({}), "")

    def test_volume_is_expressed_as_a_factor(self):
        chain = audio_processor.build_effects_filter_chain({"volume": 250})
        self.assertEqual(chain, "volume=2.5")

    def test_bass_boost_maps_100_percent_to_20_db(self):
        chain = audio_processor.build_effects_filter_chain({"bass_boost": 100})
        self.assertEqual(chain, "bass=g=20.0")

    def test_speed_sets_rate_and_resamples(self):
        chain = audio_processor.build_effects_filter_chain({"speed": 150})
        self.assertEqual(chain, "asetrate=44100*1.5,aresample=44100")

    def test_reverb_maps_to_aecho_delay_and_decay(self):
        chain = audio_processor.build_effects_filter_chain({"reverb": 100})
        self.assertEqual(chain, "aecho=0.8:0.9:200:0.7")

    def test_volume_is_always_the_last_filter(self):
        chain = audio_processor.build_effects_filter_chain(
            {"volume": 200, "speed": 150, "bass_boost": 50, "reverb": 50}
        )
        self.assertTrue(chain.endswith("volume=2.0"))
        self.assertLess(chain.index("bass=g="), chain.index("asetrate="))
        self.assertLess(chain.index("asetrate="), chain.index("aecho="))


class TestBuildEffectsFfmpegArgs(unittest.TestCase):
    def test_stream_copy_when_no_filters(self):
        args = audio_processor.build_effects_ffmpeg_args({}, "in.wav", "out.wav")
        self.assertEqual(args, ["-y", "-i", "in.wav", "-c", "copy", "out.wav"])

    def test_filter_chain_replaces_stream_copy(self):
        args = audio_processor.build_effects_ffmpeg_args({"volume": 50}, "in.wav", "out.wav")
        self.assertNotIn("copy", args)
        self.assertEqual(args[args.index("-filter:a") + 1], "volume=0.5")

    def test_trim_options_come_before_the_input(self):
        args = audio_processor.build_effects_ffmpeg_args(
            {"trim_start_sec": 1.5, "trim_end_sec": 4.0}, "in.wav", "out.wav"
        )
        self.assertLess(args.index("-ss"), args.index("-i"))
        self.assertLess(args.index("-to"), args.index("-i"))
        self.assertEqual(args[args.index("-ss") + 1], "1.5")
        self.assertEqual(args[args.index("-to") + 1], "4.0")

    def test_neutral_trim_is_omitted(self):
        args = audio_processor.build_effects_ffmpeg_args(
            {"trim_start_sec": 0, "trim_end_sec": None}, "in.wav", "out.wav"
        )
        self.assertNotIn("-ss", args)
        self.assertNotIn("-to", args)


class TestResolvePlaybackFile(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.existing = os.path.join(self.tmpdir, "fx.wav")
        with open(self.existing, "wb") as f:
            f.write(b"\x00")

    def test_prefers_the_effects_cache_when_it_exists(self):
        sound = {"filename": "orig.wav", "cached_effects_file": self.existing}
        self.assertEqual(audio_processor.resolve_playback_file(sound), self.existing)

    def test_falls_back_to_the_original_when_the_cache_is_missing(self):
        sound = {"filename": "orig.wav", "cached_effects_file": "gone.wav"}
        self.assertEqual(audio_processor.resolve_playback_file(sound), "orig.wav")

    def test_falls_back_when_no_cache_key_at_all(self):
        self.assertEqual(
            audio_processor.resolve_playback_file({"filename": "orig.wav"}), "orig.wav"
        )


@unittest.skipUnless(
    os.path.exists(audio_processor.FFMPEG_PATH), "ffmpeg binary not available"
)
class TestGenerateEffectsCache(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.wav_path = os.path.join(self.tmpdir, "tone.wav")
        with wave.open(self.wav_path, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(44100)
            w.writeframes((10000).to_bytes(2, "little", signed=True) * 44100)

    def test_renders_a_deterministic_per_sound_path(self):
        sound = {"id": "abc123", "filename": self.wav_path}
        out = audio_processor.generate_effects_cache(sound, self.tmpdir, with_peaks=False)
        self.assertEqual(out, os.path.join(self.tmpdir, "abc123_fx.wav"))
        self.assertTrue(os.path.exists(out))

    def test_rerender_overwrites_the_same_path(self):
        sound = {"id": "abc123", "filename": self.wav_path, "volume": 50}
        first = audio_processor.generate_effects_cache(sound, self.tmpdir, with_peaks=False)
        sound["volume"] = 200
        second = audio_processor.generate_effects_cache(sound, self.tmpdir, with_peaks=False)
        self.assertEqual(first, second)

    def test_trim_shortens_the_output(self):
        sound = {"id": "trimmed", "filename": self.wav_path, "trim_end_sec": 0.3}
        out = audio_processor.generate_effects_cache(sound, self.tmpdir, with_peaks=False)
        with wave.open(out, "rb") as w:
            duration = w.getnframes() / w.getframerate()
        self.assertLess(duration, 0.6)

    def test_with_peaks_writes_the_peaks_file(self):
        sound = {"id": "peaky", "filename": self.wav_path}
        out = audio_processor.generate_effects_cache(sound, self.tmpdir, with_peaks=True)
        self.assertTrue(os.path.exists(out + ".peaks.json"))

    def test_suffix_selects_a_separate_preview_file(self):
        sound = {"id": "abc123", "filename": self.wav_path}
        out = audio_processor.generate_effects_cache(
            sound, self.tmpdir, suffix="_preview", with_peaks=False
        )
        self.assertTrue(out.endswith("abc123_preview.wav"))


if __name__ == "__main__":
    unittest.main()
