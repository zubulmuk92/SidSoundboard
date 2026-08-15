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


if __name__ == "__main__":
    unittest.main()
