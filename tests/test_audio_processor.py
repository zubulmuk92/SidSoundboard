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

    def test_no_limiter_when_no_effect_is_active(self):
        chain = audio_processor.build_effects_filter_chain({"volume": 100})
        self.assertNotIn("alimiter", chain)

    def test_volume_is_expressed_as_a_factor(self):
        chain = audio_processor.build_effects_filter_chain({"volume": 250})
        self.assertEqual(chain, "volume=2.5,alimiter=limit=0.95:level=disabled")

    def test_bass_boost_maps_100_percent_to_20_db(self):
        chain = audio_processor.build_effects_filter_chain({"bass_boost": 100})
        self.assertEqual(chain, "bass=g=20.0,alimiter=limit=0.95:level=disabled")

    def test_speed_sets_rate_and_resamples(self):
        chain = audio_processor.build_effects_filter_chain({"speed": 150})
        self.assertEqual(chain, "asetrate=44100*1.5,aresample=44100,alimiter=limit=0.95:level=disabled")

    def test_reverb_maps_to_aecho_delay_and_decay(self):
        chain = audio_processor.build_effects_filter_chain({"reverb": 100})
        self.assertEqual(chain, "aecho=0.8:0.9:200:0.7,alimiter=limit=0.95:level=disabled")

    def test_volume_is_always_the_last_filter(self):
        chain = audio_processor.build_effects_filter_chain(
            {"volume": 200, "speed": 150, "bass_boost": 50, "reverb": 50}
        )
        self.assertTrue(chain.endswith("volume=2.0,alimiter=limit=0.95:level=disabled"))
        self.assertLess(chain.index("bass=g="), chain.index("asetrate="))
        self.assertLess(chain.index("asetrate="), chain.index("aecho="))


class TestBuildEffectsFfmpegArgs(unittest.TestCase):
    def test_stream_copy_when_no_filters(self):
        args = audio_processor.build_effects_ffmpeg_args({}, "in.wav", "out.wav")
        self.assertEqual(args, ["-y", "-i", "in.wav", "-c", "copy", "out.wav"])

    def test_filter_chain_replaces_stream_copy(self):
        args = audio_processor.build_effects_ffmpeg_args({"volume": 50}, "in.wav", "out.wav")
        self.assertNotIn("copy", args)
        self.assertEqual(args[args.index("-filter:a") + 1], "volume=0.5,alimiter=limit=0.95:level=disabled")

    def test_trim_options_come_before_the_input(self):
        args = audio_processor.build_effects_ffmpeg_args(
            {"trim_start_sec": 1.5, "trim_end_sec": 4.0}, "in.wav", "out.wav"
        )
        self.assertLess(args.index("-ss"), args.index("-i"))
        self.assertLess(args.index("-to"), args.index("-i"))
        self.assertEqual(args[args.index("-ss") + 1], "1.5")
        self.assertEqual(args[args.index("-to") + 1], "4.0")

    def test_trim_without_effects_reencodes_instead_of_stream_copying(self):
        args = audio_processor.build_effects_ffmpeg_args(
            {"trim_end_sec": 4.0}, "in.wav", "out.wav"
        )
        self.assertNotIn("copy", args)
        self.assertEqual(args[args.index("-c:a") + 1], "pcm_s16le")

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

    def test_trim_is_sample_accurate(self):
        sound = {
            "id": "trimmed", "filename": self.wav_path,
            "trim_start_sec": 0.25, "trim_end_sec": 0.75,
        }
        out = audio_processor.generate_effects_cache(sound, self.tmpdir, with_peaks=False)
        with wave.open(out, "rb") as w:
            duration = w.getnframes() / w.getframerate()
        self.assertAlmostEqual(duration, 0.5, places=2)

    def test_a_heavy_boost_stays_below_full_scale(self):
        sound = {"id": "loud", "filename": self.wav_path, "volume": 400, "bass_boost": 100}
        out = audio_processor.generate_effects_cache(sound, self.tmpdir, with_peaks=False)
        self.assertLess(max(audio_processor.generate_peaks(out, 20)), 1.0)

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


class TestResolveSecondaryFile(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.fx = os.path.join(self.tmpdir, "a_fx.wav")
        self.sec = os.path.join(self.tmpdir, "a_sec.wav")
        for p in (self.fx, self.sec):
            with open(p, "wb") as f:
                f.write(b"\x00")

    def test_prefers_the_secondary_cache(self):
        sound = {"filename": "o.wav", "cached_effects_file": self.fx,
                 "cached_secondary_file": self.sec}
        self.assertEqual(audio_processor.resolve_secondary_file(sound), self.sec)

    def test_falls_back_to_the_effects_cache(self):
        sound = {"filename": "o.wav", "cached_effects_file": self.fx}
        self.assertEqual(audio_processor.resolve_secondary_file(sound), self.fx)

    def test_falls_back_when_the_secondary_cache_vanished(self):
        sound = {"filename": "o.wav", "cached_effects_file": self.fx,
                 "cached_secondary_file": os.path.join(self.tmpdir, "gone.wav")}
        self.assertEqual(audio_processor.resolve_secondary_file(sound), self.fx)


@unittest.skipUnless(
    os.path.exists(audio_processor.FFMPEG_PATH), "ffmpeg binary not available"
)
class TestSecondaryCacheAndEnsure(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.wav_path = os.path.join(self.tmpdir, "tone.wav")
        with wave.open(self.wav_path, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(44100)
            w.writeframes((8000).to_bytes(2, "little", signed=True) * 44100)

    def _peak(self, path):
        return max(audio_processor.generate_peaks(path, 20))

    def test_secondary_cache_is_attenuated(self):
        sound = {"id": "s", "filename": self.wav_path}
        sound["cached_effects_file"] = audio_processor.generate_effects_cache(
            sound, self.tmpdir, with_peaks=False
        )
        sec = audio_processor.generate_secondary_cache(sound, 50, self.tmpdir)
        self.assertTrue(sec.endswith("s_sec.wav"))
        self.assertAlmostEqual(
            self._peak(sec), self._peak(sound["cached_effects_file"]) / 2, places=2
        )

    def test_no_secondary_cache_at_full_volume(self):
        sound = {"id": "s", "filename": self.wav_path}
        sound["cached_effects_file"] = audio_processor.generate_effects_cache(
            sound, self.tmpdir, with_peaks=False
        )
        self.assertIsNone(audio_processor.generate_secondary_cache(sound, 100, self.tmpdir))

    def test_ensure_caches_renders_a_missing_effects_cache(self):
        sound = {"id": "m", "filename": self.wav_path}
        changed = audio_processor.ensure_caches(sound, {}, self.tmpdir)
        self.assertTrue(changed)
        self.assertTrue(os.path.exists(sound["cached_effects_file"]))

    def test_ensure_caches_is_a_no_op_when_everything_is_present(self):
        sound = {"id": "m", "filename": self.wav_path}
        audio_processor.ensure_caches(sound, {}, self.tmpdir)
        self.assertFalse(audio_processor.ensure_caches(sound, {}, self.tmpdir))

    def test_ensure_caches_rerenders_when_the_secondary_volume_changed(self):
        sound = {"id": "m", "filename": self.wav_path}
        audio_processor.ensure_caches(sound, {"global_secondary_volume": 50}, self.tmpdir)
        self.assertTrue(os.path.exists(sound["cached_secondary_file"]))
        self.assertFalse(
            audio_processor.ensure_caches(sound, {"global_secondary_volume": 50}, self.tmpdir)
        )
        self.assertTrue(
            audio_processor.ensure_caches(sound, {"global_secondary_volume": 20}, self.tmpdir)
        )

    def test_ensure_caches_drops_the_secondary_cache_at_full_volume(self):
        sound = {"id": "m", "filename": self.wav_path}
        audio_processor.ensure_caches(sound, {"global_secondary_volume": 50}, self.tmpdir)
        audio_processor.ensure_caches(sound, {"global_secondary_volume": 100}, self.tmpdir)
        self.assertIsNone(sound["cached_secondary_file"])


if __name__ == "__main__":
    unittest.main()
