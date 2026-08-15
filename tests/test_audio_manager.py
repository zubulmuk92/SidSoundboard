import array
import unittest

import audio_manager


def make_constant_source(amplitude, nchannels, chunk_frames, total_chunks):
    def gen():
        for _ in range(total_chunks):
            yield array.array('h', [amplitude] * (chunk_frames * nchannels))
    return gen()


class TestFadingStream(unittest.TestCase):
    def test_no_fade_passes_through_unchanged(self):
        source = make_constant_source(1000, 1, 10, 5)
        state = audio_manager.FadeState()
        stream = audio_manager.FadingStream(
            source, sample_rate=100, nchannels=1,
            fade_in_ms=0, fade_out_ms=0, total_frames=50, fade_state=state
        )
        chunk = next(stream)
        self.assertEqual(list(chunk), [1000] * 10)

    def test_fade_in_ramps_from_zero(self):
        source = make_constant_source(1000, 1, 10, 5)
        state = audio_manager.FadeState()
        stream = audio_manager.FadingStream(
            source, sample_rate=100, nchannels=1,
            fade_in_ms=100, fade_out_ms=0, total_frames=50, fade_state=state
        )
        chunk = next(stream)
        self.assertEqual(chunk[0], 0)
        self.assertGreater(chunk[-1], chunk[0])

    def test_forced_stop_fades_to_zero_and_marks_finished(self):
        source = make_constant_source(1000, 1, 10, 5)
        state = audio_manager.FadeState()
        stream = audio_manager.FadingStream(
            source, sample_rate=100, nchannels=1,
            fade_in_ms=0, fade_out_ms=100, total_frames=50, fade_state=state
        )
        state.stop_requested = True
        chunk = next(stream)
        self.assertLess(chunk[-1], 1000)
        self.assertTrue(state.finished)

    def test_natural_end_fade_out_reduces_last_chunk(self):
        # total_frames=50, fade_out=100ms @ 100Hz = 10 frames.
        # Chunks of 10 frames: chunk 5 (frames 40-49) is entirely inside
        # the fade-out window.
        source = make_constant_source(1000, 1, 10, 5)
        state = audio_manager.FadeState()
        stream = audio_manager.FadingStream(
            source, sample_rate=100, nchannels=1,
            fade_in_ms=0, fade_out_ms=100, total_frames=50, fade_state=state
        )
        for _ in range(4):
            next(stream)
        last_chunk = next(stream)
        self.assertLess(last_chunk[-1], 1000)


class FakeDevice:
    def __init__(self):
        self.closed = False
        self.running = True

    def close(self):
        self.closed = True
        self.running = False


class FakeStream:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class TestStopSound(unittest.TestCase):
    def setUp(self):
        self.manager = audio_manager.AudioManager.__new__(audio_manager.AudioManager)
        self.manager.active_playbacks = []
        self.manager.focused_info = None
        self.entries = {}
        for sound_id in ("a", "b"):
            entry = (FakeDevice(), FakeStream(), audio_manager.FadeState(), sound_id)
            self.entries[sound_id] = entry
            self.manager.active_playbacks.append(entry)

    def test_stops_only_the_targeted_sound(self):
        self.assertTrue(self.manager.stop_sound("a"))
        self.assertTrue(self.entries["a"][0].closed)
        self.assertFalse(self.entries["b"][0].closed)
        self.assertEqual([e[3] for e in self.manager.active_playbacks], ["b"])

    def test_releases_the_file_stream_not_just_the_device(self):
        self.manager.stop_sound("a")
        self.assertTrue(self.entries["a"][1].closed)

    def test_clears_focus_when_it_was_the_stopped_sound(self):
        self.manager.focused_info = {"sound_id": "a"}
        self.manager.stop_sound("a")
        self.assertIsNone(self.manager.focused_info)

    def test_keeps_focus_on_a_different_sound(self):
        self.manager.focused_info = {"sound_id": "b"}
        self.manager.stop_sound("a")
        self.assertEqual(self.manager.focused_info, {"sound_id": "b"})

    def test_reports_nothing_stopped_for_an_idle_sound(self):
        self.assertFalse(self.manager.stop_sound("zzz"))
        self.assertEqual(len(self.manager.active_playbacks), 2)

    def test_a_none_id_is_a_no_op(self):
        self.assertFalse(self.manager.stop_sound(None))
        self.assertEqual(len(self.manager.active_playbacks), 2)

    def test_stop_all_also_closes_the_streams(self):
        self.manager.stop_all()
        self.assertTrue(all(e[1].closed for e in self.entries.values()))
        self.assertEqual(self.manager.active_playbacks, [])


class TestFadingStreamClose(unittest.TestCase):
    def test_close_forwards_to_the_wrapped_generator(self):
        source = make_constant_source(1000, 1, 10, 5)
        stream = audio_manager.FadingStream(
            source, sample_rate=100, nchannels=1,
            fade_in_ms=0, fade_out_ms=0, total_frames=50,
            fade_state=audio_manager.FadeState(),
        )
        stream.close()
        with self.assertRaises(StopIteration):
            next(source)


if __name__ == "__main__":
    unittest.main()
