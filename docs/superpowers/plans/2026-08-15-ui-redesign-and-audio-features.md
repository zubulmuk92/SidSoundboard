# SidSoundboard UI Redesign & Audio Features Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the unstable single-file `gui_pyside.py` with a modular, visually distinctive PySide6 UI (`ui/` package), add a precomputed waveform display and fade-in/out/crossfade playback, and fix three real correctness bugs discovered in the current code — while preserving the zero-CPU-idle / low-RAM audio engine.

**Architecture:** The audio engine (`audio_manager.py`, `audio_processor.py`, `hotkey_manager.py`) stays in place and gets targeted extensions (fade envelope generator, peak extraction). The UI is rebuilt from scratch as a `ui/` package with clear boundaries: `theme.py` (visual system), `widgets/` (reusable, signal-based components), `views/` (screens), `main_window.py` (assembly + engine wiring).

**Tech Stack:** Python, PySide6 (Qt), `miniaudio` (streaming playback + decode), FFmpeg (subprocess, via `audio_processor.py`), `keyboard` (global hotkeys), `pystray` (system tray), `yt-dlp` (YouTube import), `unittest` (stdlib, no new test dependency).

**Spec:** [docs/superpowers/specs/2026-08-15-soundboard-redesign-design.md](../specs/2026-08-15-soundboard-redesign-design.md)

## Global Constraints

- Zero CPU usage at idle and during steady-state playback (outside fade windows) — no per-sample processing unless a fade is actively in progress.
- RAM baseline stays low (<30 Mo) — audio is streamed from disk, never fully loaded into memory for playback (peak extraction for waveform is the one exception: it fully decodes a file, but only once at import time, in a background thread, and discards the decoded buffer immediately after).
- Windows target (`sys._MEIPASS` / PyInstaller packaging paths already used throughout — follow the same `resource_path` pattern for any new file lookup).
- UI strings stay in French, matching all existing user-facing text.
- Visual system: background `#121316`/`#1B1D21`/`#26292F`, accent `#FF8A3D`, text `#F2F1ED`/`#8B8D93`, existing category tag colors unchanged (see `ui/theme.py` in Task 6).
- Sound dict schema is standardized to keys: `id`, `name`, `filename`, `hotkey`, `volume`, `color` — some existing code reads a `file` key instead of `filename`, or writes settings under different key names than playback reads (`default_device`/`second_device` vs `primary_output`/`secondary_output`); these are real bugs fixed in Task 2 and Task 10, not incidental refactors. Do not reintroduce the old key names.

---

## File Structure

```
ui/
  __init__.py                 # empty
  theme.py                    # colors, QSS, get_icon()/resource_path()
  main_window.py               # AppGUI(QMainWindow) — assembly + engine wiring
  views/
    __init__.py                # empty
    library_view.py             # sound grid, search, import, YouTube dialog
    settings_view.py            # devices, dual-output toggle, ducking, fades, panic key
  widgets/
    __init__.py                # empty
    waveform.py                  # WaveformWidget + peaks loading helper
    sound_card.py                 # SoundCard(QFrame) — one sound in the grid
    player_bar.py                 # PlayerBar(QFrame) — bottom transport bar
tests/
  __init__.py                 # empty
  test_audio_processor.py      # peak extraction
  test_audio_manager.py         # fade envelope
  test_hotkey_manager.py         # callback key-name fix
```

Modified: `audio_processor.py`, `audio_manager.py`, `hotkey_manager.py`, `config_manager.py`, `main.py`, `SidSoundboard.spec`, `.gitignore`.

Deleted: `gui_pyside.py`, `patch_gui.py`, `test_import.py`, `test_qt.py`, `test_miniaudio2.py`.

---

### Task 1: Repository cleanup

**Files:**
- Delete: `patch_gui.py`, `test_import.py`, `test_qt.py`, `test_miniaudio2.py`
- Modify: `.gitignore`
- Commit the already-pending deletion of `gui.py` (staged as deleted in working tree)

**Interfaces:** none (no code dependencies from this task).

- [ ] **Step 1: Delete the scratch/patch files**

```bash
git rm patch_gui.py test_import.py test_qt.py test_miniaudio2.py
```

- [ ] **Step 2: Add runtime artifacts to `.gitignore`**

Add these lines to `.gitignore` (append, don't remove existing entries):

```
# Runtime artifacts
crash.log
debug.log
config.json
downloads/
*.peaks.json
```

- [ ] **Step 3: Stage and commit cleanup**

```bash
git add .gitignore gui.py
git commit -m "Remove CustomTkinter UI and migration scratch files"
```

- [ ] **Step 4: Verify working tree is clean of scratch files**

Run: `git status`
Expected: `patch_gui.py`, `test_import.py`, `test_qt.py`, `test_miniaudio2.py`, `gui.py` no longer listed; no untracked scratch files remain.

---

### Task 2: Fix hotkey registration bugs in `hotkey_manager.py`

The current code reads `sound.get("file")` to decide whether to register a
hotkey, but every sound dict actually stores its path under `filename`.
Since `file` is never set, `filepath` is always `None`, so the `if hotkey
and filepath:` guard is always false — **no hotkey is ever registered
today**. Separately, the "unset" hotkey sentinel value is the string
`"None"` (set by the GUI), which was never filtered out.

**Files:**
- Modify: `hotkey_manager.py`
- Test: `tests/test_hotkey_manager.py`

**Interfaces:**
- Produces: `HotkeyManager._should_register(sound: dict) -> bool` (static method), `HotkeyManager._play_sound_callback(sound: dict) -> None` (reads `sound["filename"]`, calls `self.audio_manager.toggle_play_pause(...)`).

- [ ] **Step 1: Create the tests directory**

```bash
mkdir -p tests
```

Create `tests/__init__.py` (empty file).

- [ ] **Step 2: Write the failing tests**

Create `tests/test_hotkey_manager.py`:

```python
import unittest
from unittest.mock import MagicMock

from hotkey_manager import HotkeyManager


class TestShouldRegister(unittest.TestCase):
    def test_true_when_hotkey_and_filename_set(self):
        self.assertTrue(
            HotkeyManager._should_register({"hotkey": "f1", "filename": "x.wav"})
        )

    def test_false_when_hotkey_is_none_sentinel(self):
        self.assertFalse(
            HotkeyManager._should_register({"hotkey": "None", "filename": "x.wav"})
        )

    def test_false_when_no_filename(self):
        self.assertFalse(
            HotkeyManager._should_register({"hotkey": "f1", "filename": None})
        )

    def test_false_when_no_hotkey(self):
        self.assertFalse(
            HotkeyManager._should_register({"hotkey": None, "filename": "x.wav"})
        )


class TestPlaySoundCallback(unittest.TestCase):
    def test_uses_filename_key_and_forwards_sound_id(self):
        audio_manager = MagicMock()
        config = {
            "sounds": [], "primary_output": "Speakers",
            "secondary_output": None, "dual_output_enabled": False,
        }
        manager = HotkeyManager(audio_manager, config)

        sound = {
            "id": "abc123", "name": "Test", "filename": "C:/sounds/test.wav",
            "hotkey": "f1", "volume": 100,
        }
        manager._play_sound_callback(sound)

        audio_manager.toggle_play_pause.assert_called_once()
        _, kwargs = audio_manager.toggle_play_pause.call_args
        self.assertEqual(kwargs["filepath_primary"], "C:/sounds/test.wav")
        self.assertEqual(kwargs["sound_id"], "abc123")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `python -m unittest tests.test_hotkey_manager -v`
Expected: `AttributeError` — `_should_register` does not exist yet, and
`_play_sound_callback` reads the wrong key so `filepath_primary` won't
match.

- [ ] **Step 4: Fix `hotkey_manager.py`**

Replace the body of `load_hotkeys` and `_play_sound_callback` in
`hotkey_manager.py`:

```python
    def load_hotkeys(self, config):
        self.config = config
        self._clear_hotkeys()

        if self.config.get("panic_key"):
            try:
                self.panic_hook = keyboard.on_press_key(self.config["panic_key"], self._panic_callback)
            except Exception as e:
                print(f"Failed to register panic key: {e}")

        for sound in self.config.get("sounds", []):
            if self._should_register(sound):
                try:
                    hk = keyboard.add_hotkey(sound["hotkey"], self._play_sound_callback, args=(sound,))
                    self.registered_hotkeys.append(hk)
                except Exception as e:
                    print(f"Failed to register hotkey {sound['hotkey']}: {e}")

    @staticmethod
    def _should_register(sound):
        hotkey = sound.get("hotkey")
        filepath = sound.get("filename")
        return bool(hotkey) and hotkey != "None" and bool(filepath)
```

```python
    def _play_sound_callback(self, sound):
        vol_p = sound.get("volume", 100)
        spd = sound.get("speed", 100)
        global_sec_vol = self.config.get("global_secondary_volume", 100)
        vol_s = int(vol_p * (global_sec_vol / 100.0))

        original_file = sound.get("filename")
        from audio_processor import generate_cached_file_sync
        try:
            filepath_sec = generate_cached_file_sync(original_file, vol_s, spd)
        except Exception:
            filepath_sec = original_file

        if self.config.get("mode_solo", False):
            self.audio_manager.stop_all()

        self.audio_manager.toggle_play_pause(
            filepath_primary=sound.get("cached_file_primary") or sound.get("cached_file") or original_file,
            filepath_secondary=filepath_sec,
            name=sound.get("name", "Unknown"),
            volume=1.0,
            primary_device_name=self.config.get("primary_output"),
            secondary_device_name=self.config.get("secondary_output"),
            dual_enabled=self.config.get("dual_output_enabled", False),
            sound_id=sound.get("id")
        )
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python -m unittest tests.test_hotkey_manager -v`
Expected: `OK` (4 + 1 tests pass).

- [ ] **Step 6: Commit**

```bash
git add hotkey_manager.py tests/__init__.py tests/test_hotkey_manager.py
git commit -m "Fix hotkey registration: read filename key, filter None sentinel"
```

---

### Task 3: Waveform peak extraction in `audio_processor.py`

**Files:**
- Modify: `audio_processor.py`
- Test: `tests/test_audio_processor.py`

**Interfaces:**
- Produces: `generate_peaks(filepath: str, num_buckets: int = 200) -> list[float]` (values normalized 0.0-1.0), `generate_and_save_peaks(filepath: str, num_buckets: int = 200) -> str` (returns the path to the written `<filepath>.peaks.json`, containing `{"peaks": [...]}`).

- [ ] **Step 1: Write the failing tests**

Create `tests/test_audio_processor.py`:

```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m unittest tests.test_audio_processor -v`
Expected: `AttributeError: module 'audio_processor' has no attribute 'generate_peaks'`

- [ ] **Step 3: Implement `generate_peaks` and `generate_and_save_peaks`**

Add to the top of `audio_processor.py` (alongside the existing `import os`,
`import sys`, `import subprocess`, `import threading`):

```python
import json
```

Append to `audio_processor.py`:

```python
def generate_peaks(filepath, num_buckets=200):
    """
    Decodes the file once (mono) and reduces it to num_buckets normalized
    peak values (0.0-1.0), for a lightweight waveform preview. Only ever
    called once, at import time, from a background thread.
    """
    import miniaudio
    decoded = miniaudio.decode_file(filepath, nchannels=1)
    samples = decoded.samples
    total = len(samples)
    if total == 0:
        return [0.0] * num_buckets

    bucket_size = max(1, total // num_buckets)
    peaks = []
    for i in range(0, total, bucket_size):
        chunk = samples[i:i + bucket_size]
        if not chunk:
            continue
        peak = max(abs(s) for s in chunk) / 32768.0
        peaks.append(min(1.0, peak))

    if len(peaks) < num_buckets:
        peaks.extend([0.0] * (num_buckets - len(peaks)))
    else:
        peaks = peaks[:num_buckets]
    return peaks


def generate_and_save_peaks(filepath, num_buckets=200):
    peaks = generate_peaks(filepath, num_buckets)
    peaks_path = filepath + ".peaks.json"
    with open(peaks_path, "w", encoding="utf-8") as f:
        json.dump({"peaks": peaks}, f)
    return peaks_path
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m unittest tests.test_audio_processor -v`
Expected: `OK` (4 tests pass).

- [ ] **Step 5: Commit**

```bash
git add audio_processor.py tests/test_audio_processor.py
git commit -m "Add waveform peak extraction (generate_peaks, generate_and_save_peaks)"
```

---

### Task 4: Fade envelope engine in `audio_manager.py`

Introduces `FadeState` (a shared trigger object) and `FadingStream` (a
wrapper around a `miniaudio.stream_file` generator that applies a linear
gain ramp only inside fade windows, and passes chunks through unmodified
otherwise). This task only adds the classes and tests them in isolation
with a fake source — it does not yet wire them into playback (Task 5).

**Files:**
- Modify: `audio_manager.py`
- Test: `tests/test_audio_manager.py`

**Interfaces:**
- Produces: `FadeState()` (attributes: `stop_requested: bool`, `finished: bool`, both default `False`), `FadingStream(source, sample_rate: int, nchannels: int, fade_in_ms: int, fade_out_ms: int, total_frames: int, fade_state: FadeState)` — object supporting `next(stream)` and `stream.send(n)`, mirroring the generator protocol `miniaudio.stream_file` already uses.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_audio_manager.py`:

```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m unittest tests.test_audio_manager -v`
Expected: `AttributeError: module 'audio_manager' has no attribute 'FadeState'`

- [ ] **Step 3: Implement `FadeState` and `FadingStream`**

Add `import array` to the top of `audio_manager.py` (alongside the existing
`import miniaudio`, `import time`). Then append these two classes:

```python
class FadeState:
    """Shared trigger object: set stop_requested to start an early fade-out."""
    def __init__(self):
        self.stop_requested = False
        self.finished = False


class FadingStream:
    """
    Wraps a miniaudio.stream_file generator. Applies a linear gain ramp
    during fade-in (first fade_in_ms), fade-out (last fade_out_ms of a
    known-duration stream, via total_frames), or a forced fade-out
    (triggered externally via fade_state.stop_requested, e.g. for a
    crossfade). Outside those windows, chunks pass through untouched —
    zero extra cost in steady-state playback.
    """
    def __init__(self, source, sample_rate, nchannels, fade_in_ms, fade_out_ms, total_frames, fade_state):
        self.source = source
        self.nchannels = nchannels
        self.fade_in_frames = int(sample_rate * fade_in_ms / 1000)
        self.fade_out_frames = int(sample_rate * fade_out_ms / 1000)
        self.total_frames = total_frames
        self.fade_state = fade_state
        self.frame_pos = 0
        self.forced_fade_start = None

    def __next__(self):
        return self._process(next(self.source))

    def send(self, n_frames):
        return self._process(self.source.send(n_frames))

    def _process(self, chunk):
        n = len(chunk) // self.nchannels
        if n == 0:
            return chunk

        if self.fade_state.stop_requested and self.forced_fade_start is None:
            self.forced_fade_start = self.frame_pos

        needs_processing = False
        if self.fade_in_frames > 0 and self.frame_pos < self.fade_in_frames:
            needs_processing = True
        if self.forced_fade_start is not None:
            needs_processing = True
        elif self.fade_out_frames > 0 and self.total_frames > 0 and (self.frame_pos + n) > self.total_frames - self.fade_out_frames:
            needs_processing = True

        if not needs_processing:
            self.frame_pos += n
            return chunk

        out = array.array(chunk.typecode, chunk)
        for i in range(n):
            pos = self.frame_pos + i
            gain = 1.0
            if self.fade_in_frames > 0 and pos < self.fade_in_frames:
                gain = min(gain, pos / self.fade_in_frames)
            if self.forced_fade_start is not None:
                elapsed = pos - self.forced_fade_start
                if self.fade_out_frames > 0:
                    gain = min(gain, max(0.0, 1.0 - elapsed / self.fade_out_frames))
                else:
                    gain = 0.0
            elif self.fade_out_frames > 0 and self.total_frames > 0:
                remaining = self.total_frames - pos
                if remaining < self.fade_out_frames:
                    gain = min(gain, max(0.0, remaining / self.fade_out_frames))
            if gain < 1.0:
                base = i * self.nchannels
                for c in range(self.nchannels):
                    out[base + c] = int(out[base + c] * gain)

        if self.forced_fade_start is not None and (self.frame_pos + n - self.forced_fade_start) >= self.fade_out_frames:
            self.fade_state.finished = True

        self.frame_pos += n
        return out
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m unittest tests.test_audio_manager -v`
Expected: `OK` (4 tests pass).

- [ ] **Step 5: Commit**

```bash
git add audio_manager.py tests/test_audio_manager.py
git commit -m "Add FadeState/FadingStream envelope generator"
```

---

### Task 5: Wire fades and dual-output config into `AudioManager`

Uses `FadeState`/`FadingStream` from Task 4 in real playback, and adds
crossfade behavior when switching sounds. This task's changes require a
real audio device to verify — no new automated test; verification is
manual (Step 6).

**Files:**
- Modify: `audio_manager.py`, `config_manager.py`

**Interfaces:**
- Consumes: `FadeState`, `FadingStream` from Task 4.
- Produces: `AudioManager.set_fade_durations(fade_in_ms: int, fade_out_ms: int) -> None`. `active_playbacks` items are now 3-tuples `(device, stream, fade_state)` (previously 2-tuples/bare devices) — this is consumed by `ui/main_window.py` in Task 10 only indirectly (through `AudioManager` methods, never by reading the tuples directly).

- [ ] **Step 1: Add fade settings and `threading` import to `AudioManager.__init__`**

Add `import threading` to the top of `audio_manager.py`. Modify
`__init__`:

```python
    def __init__(self):
        self.devices = miniaudio.Devices()
        self.active_playbacks = []
        self.focused_info = None
        self.fade_in_ms = 0
        self.fade_out_ms = 0

    def set_fade_durations(self, fade_in_ms, fade_out_ms):
        self.fade_in_ms = fade_in_ms
        self.fade_out_ms = fade_out_ms
```

- [ ] **Step 2: Wrap the stream in `_start_playback` and update its return value**

Replace `_start_playback`:

```python
    def _start_playback(self, filepath, device_id, info, seek_offset):
        try:
            device = miniaudio.PlaybackDevice(
                device_id=device_id,
                nchannels=info.nchannels,
                sample_rate=info.sample_rate
            )

            seek_frame = int(seek_offset * info.sample_rate)
            stream = miniaudio.stream_file(filepath, seek_frame=seek_frame)
            next(stream)

            fade_state = FadeState()
            if self.fade_in_ms > 0 or self.fade_out_ms > 0:
                total_frames = int(info.duration * info.sample_rate)
                stream = FadingStream(
                    stream, info.sample_rate, info.nchannels,
                    self.fade_in_ms, self.fade_out_ms, total_frames, fade_state
                )

            device.start(stream)

            self.active_playbacks.append((device, stream, fade_state))
            self._cleanup_playbacks()
            return device, fade_state
        except Exception:
            return None, None
```

- [ ] **Step 3: Update `play_sound` to unpack the new return value**

Replace the body of `play_sound` (keep the same signature):

```python
    def play_sound(self, filepath_primary, filepath_secondary, name, volume=1.0, primary_device_name=None, secondary_device_name=None, dual_enabled=False, seek_offset=0.0, sound_id=None):
        if not filepath_primary:
            return

        primary_id = None
        secondary_id = None

        for dev in self.get_output_devices():
            if dev["name"] == primary_device_name:
                primary_id = dev["id"]
            if dev["name"] == secondary_device_name:
                secondary_id = dev["id"]

        try:
            dev1 = None
            fade_state1 = None
            if filepath_primary:
                info = miniaudio.get_file_info(filepath_primary)
                dev1, fade_state1 = self._start_playback(filepath_primary, primary_id, info, seek_offset)

            if dual_enabled and secondary_id and filepath_secondary:
                info_sec = miniaudio.get_file_info(filepath_secondary)
                self._start_playback(filepath_secondary, secondary_id, info_sec, seek_offset)

            if dev1:
                self.focused_info = {
                    "sound_id": sound_id,
                    "filepath_primary": filepath_primary,
                    "filepath_secondary": filepath_secondary,
                    "name": name,
                    "duration": info.duration,
                    "start_sys_time": time.time(),
                    "seek_offset": seek_offset,
                    "primary_device_name": primary_device_name,
                    "secondary_device_name": secondary_device_name,
                    "dual_enabled": dual_enabled,
                    "device": dev1,
                    "fade_state": fade_state1,
                }

        except Exception as e:
            print(f"Erreur Audio: {str(e)}")
            try:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.critical(None, "Erreur Audio", f"Impossible de jouer le son :\n{str(e)}")
            except Exception:
                pass
```

- [ ] **Step 4: Update `stop_all` and `_cleanup_playbacks` to unpack 3-tuples, add crossfade to `toggle_play_pause`**

Replace `_cleanup_playbacks`, `stop_all`, and `toggle_play_pause`:

```python
    def _cleanup_playbacks(self):
        alive = []
        for device, stream, fade_state in self.active_playbacks:
            try:
                if device.running:
                    alive.append((device, stream, fade_state))
                else:
                    device.close()
            except Exception:
                pass
        self.active_playbacks = alive

    def stop_all(self):
        for device, stream, fade_state in self.active_playbacks:
            try:
                device.close()
            except Exception:
                pass
        self.active_playbacks.clear()
        self.focused_info = None

    def toggle_play_pause(self, filepath_primary, filepath_secondary, name, volume=1.0, primary_device_name=None, secondary_device_name=None, dual_enabled=False, sound_id=None):
        if not filepath_primary:
            return
        fi = self.focused_info

        if fi and fi.get("sound_id") == sound_id:
            if fi.get("is_paused"):
                seek = fi.get("paused_at", 0.0)
                self.stop_all()
                self.play_sound(filepath_primary, filepath_secondary, name, volume, primary_device_name, secondary_device_name, dual_enabled, seek, sound_id)
            else:
                prog = self.get_focused_progress()
                if prog:
                    paused_at = prog["current"]
                    for device, stream, fade_state in self.active_playbacks:
                        try:
                            device.close()
                        except Exception:
                            pass
                    self.active_playbacks.clear()
                    fi["is_paused"] = True
                    fi["paused_at"] = paused_at
                    self.focused_info = fi
            return

        if fi and self.fade_out_ms > 0 and self.active_playbacks:
            self._crossfade_to(filepath_primary, filepath_secondary, name, volume, primary_device_name, secondary_device_name, dual_enabled, sound_id)
        else:
            self.stop_all()
            self.play_sound(filepath_primary, filepath_secondary, name, volume, primary_device_name, secondary_device_name, dual_enabled, 0.0, sound_id)

    def _crossfade_to(self, filepath_primary, filepath_secondary, name, volume, primary_device_name, secondary_device_name, dual_enabled, sound_id):
        outgoing = list(self.active_playbacks)
        for device, stream, fade_state in outgoing:
            fade_state.stop_requested = True

        self.active_playbacks = []
        self.play_sound(filepath_primary, filepath_secondary, name, volume, primary_device_name, secondary_device_name, dual_enabled, 0.0, sound_id)

        def close_outgoing():
            for device, stream, fade_state in outgoing:
                try:
                    device.close()
                except Exception:
                    pass

        delay = (self.fade_out_ms / 1000.0) + 0.1
        timer = threading.Timer(delay, close_outgoing)
        timer.daemon = True
        timer.start()
```

- [ ] **Step 5: Add fade duration and consistent output-device keys to `config_manager.py`**

Update `DEFAULT_CONFIG` in `config_manager.py`:

```python
DEFAULT_CONFIG = {
    "sounds": [],
    "panic_key": "pause",
    "panic_hotkey": "None",
    "main_volume": 1.0,
    "primary_output": None,
    "secondary_output": None,
    "dual_output_enabled": False,
    "audio_ducking_level": "Léger (50%)",
    "fade_in_ms": 150,
    "fade_out_ms": 150,
}
```

- [ ] **Step 6: Manual verification**

Run: `python -c "import audio_manager, config_manager; am = audio_manager.AudioManager(); am.set_fade_durations(150, 150); print('OK', am.fade_in_ms, am.fade_out_ms)"`
Expected: prints `OK 150 150` with no traceback (confirms the module still imports and wires correctly; full audio playback is verified end-to-end in Task 13 once the UI can trigger it).

- [ ] **Step 7: Commit**

```bash
git add audio_manager.py config_manager.py
git commit -m "Wire fade envelope and crossfade into AudioManager playback"
```

---

### Task 6: Visual theme — `ui/theme.py`

**Files:**
- Create: `ui/__init__.py` (empty)
- Create: `ui/theme.py`

**Interfaces:**
- Produces: `resource_path(relative_path: str) -> str`, `get_icon(name: str) -> QIcon`, `QSS: str`, color constants `BG_APP`, `BG_PANEL`, `BG_HOVER`, `TEXT_MAIN`, `TEXT_MUTED`, `ACCENT`, `ACCENT_HOVER`, `DANGER`, `CATEGORY_COLORS: dict[str, str]`.

- [ ] **Step 1: Create `ui/__init__.py`**

Empty file.

- [ ] **Step 2: Create `ui/theme.py`**

```python
import os
import sys

from PySide6.QtGui import QIcon


def resource_path(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_path, relative_path)


def get_icon(name):
    return QIcon(os.path.join(resource_path("icons"), name))


BG_APP = "#121316"
BG_PANEL = "#1B1D21"
BG_HOVER = "#26292F"
TEXT_MAIN = "#F2F1ED"
TEXT_MUTED = "#8B8D93"
ACCENT = "#FF8A3D"
ACCENT_HOVER = "#E67227"
DANGER = "#EF4444"

CATEGORY_COLORS = {
    "Sons Troll": "#FF3366",
    "Musiques": "#33CCFF",
    "SFX": "#33FF99",
    "Voix": "#FFCC00",
    "Ambiance": "#B829FF",
    "Gris": "#8B8D93",
}

QSS = f"""
QMainWindow, QDialog {{ background-color: {BG_APP}; }}
QWidget {{ color: {TEXT_MAIN}; font-family: 'Inter', 'Segoe UI'; font-size: 13px; }}

QScrollArea {{ border: none; background-color: transparent; }}
QScrollArea > QWidget > QWidget {{ background-color: transparent; }}

QScrollBar:vertical {{ border: none; background: {BG_APP}; width: 10px; }}
QScrollBar::handle:vertical {{ background: {BG_HOVER}; min-height: 20px; border-radius: 5px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ border: none; background: none; }}

QPushButton {{
    background-color: {BG_PANEL}; color: {TEXT_MAIN}; border: 1px solid {BG_APP};
    border-radius: 6px; padding: 6px 12px; font-weight: 600;
}}
QPushButton:hover {{ background-color: {BG_HOVER}; border: 1px solid {ACCENT}; }}
QPushButton.accent {{ background-color: {ACCENT}; color: #121316; border: none; }}
QPushButton.accent:hover {{ background-color: {ACCENT_HOVER}; }}
QPushButton.danger {{ background-color: transparent; border: 1px solid {DANGER}; color: {DANGER}; }}
QPushButton.danger:hover {{ background-color: {DANGER}; color: white; }}

QLineEdit, QComboBox {{
    background-color: {BG_PANEL}; color: {TEXT_MAIN}; border: 1px solid {BG_HOVER};
    border-radius: 6px; padding: 6px 10px;
}}
QLineEdit:focus, QComboBox:focus {{ border: 1px solid {ACCENT}; }}
QComboBox::drop-down {{ border: none; }}
QComboBox QAbstractItemView {{ background-color: {BG_PANEL}; color: {TEXT_MAIN}; selection-background-color: {ACCENT}; }}

QSlider::groove:horizontal {{ border: 1px solid {BG_PANEL}; background: {BG_APP}; height: 6px; border-radius: 3px; }}
QSlider::handle:horizontal {{ background: {ACCENT}; width: 14px; margin-top: -4px; margin-bottom: -4px; border-radius: 7px; }}

#Sidebar {{ background-color: {BG_PANEL}; border-right: 1px solid {BG_APP}; }}
#Sidebar QPushButton {{ background-color: transparent; border: none; text-align: left; padding-left: 20px; font-size: 14px; }}
#Sidebar QPushButton:hover {{ background-color: {BG_HOVER}; }}
#Sidebar QPushButton:checked {{ background-color: {BG_APP}; color: {ACCENT}; border-left: 3px solid {ACCENT}; border-radius: 0px; }}

#SoundCard {{ background-color: {BG_PANEL}; border: 1px solid {BG_APP}; border-radius: 8px; }}
#SoundCard:hover {{ background-color: {BG_HOVER}; border: 1px solid {ACCENT}; }}

QProgressBar {{ border: 1px solid {BG_APP}; border-radius: 4px; text-align: center; color: white; background: {BG_PANEL}; }}
QProgressBar::chunk {{ background-color: {ACCENT}; width: 1px; }}
"""
```

- [ ] **Step 3: Verify it imports cleanly**

Run: `python -c "from ui.theme import QSS, ACCENT, get_icon; print(len(QSS), ACCENT)"`
Expected: prints a number and `#FF8A3D`, no traceback.

- [ ] **Step 4: Commit**

```bash
git add ui/__init__.py ui/theme.py
git commit -m "Add ui package with visual theme system"
```

---

### Task 7: `WaveformWidget`

**Files:**
- Create: `ui/widgets/__init__.py` (empty)
- Create: `ui/widgets/waveform.py`

**Interfaces:**
- Consumes: nothing from earlier UI tasks (only stdlib `json`/`os` and PySide6).
- Produces: `load_peaks(peaks_path: str) -> list[float]` (returns `[]` if missing/unreadable), `WaveformWidget(color: str = "#FF8A3D", interactive: bool = False, parent=None)` — a `QWidget` with methods `set_peaks(peaks: list[float])`, `set_progress(ratio: float)`, and signal `seek_requested(float)` (emitted only when `interactive=True`, on click, with the click's x-ratio 0.0-1.0).

- [ ] **Step 1: Create `ui/widgets/__init__.py`**

Empty file.

- [ ] **Step 2: Create `ui/widgets/waveform.py`**

```python
import json
import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


def load_peaks(peaks_path):
    if not peaks_path or not os.path.exists(peaks_path):
        return []
    try:
        with open(peaks_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("peaks", [])
    except (OSError, ValueError):
        return []


class WaveformWidget(QWidget):
    seek_requested = Signal(float)

    def __init__(self, color="#FF8A3D", interactive=False, parent=None):
        super().__init__(parent)
        self.peaks = []
        self.progress = 0.0
        self.base_color = QColor("#3A3D44")
        self.played_color = QColor(color)
        self.interactive = interactive
        self.setMinimumHeight(28)

    def set_peaks(self, peaks):
        self.peaks = peaks or []
        self.update()

    def set_progress(self, progress):
        self.progress = max(0.0, min(1.0, progress))
        self.update()

    def mousePressEvent(self, event):
        if self.interactive and self.width() > 0:
            ratio = max(0.0, min(1.0, event.position().x() / self.width()))
            self.seek_requested.emit(ratio)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height()
        mid = h / 2

        if not self.peaks:
            painter.setPen(QPen(self.base_color, 1))
            painter.drawLine(0, int(mid), w, int(mid))
            painter.end()
            return

        n = len(self.peaks)
        bar_width = max(1.0, w / n)
        split_index = int(n * self.progress)

        painter.setPen(Qt.NoPen)
        for i, amplitude in enumerate(self.peaks):
            x = i * bar_width
            bar_h = max(1.0, amplitude * (h - 4))
            painter.setBrush(self.played_color if i < split_index else self.base_color)
            painter.drawRect(int(x), int(mid - bar_h / 2), max(1, int(bar_width) - 1), int(bar_h))

        painter.end()
```

- [ ] **Step 3: Manual verification**

Run:
```bash
python -c "
from PySide6.QtWidgets import QApplication
from ui.widgets.waveform import WaveformWidget, load_peaks
app = QApplication([])
w = WaveformWidget(interactive=True)
w.set_peaks([0.1, 0.5, 0.9, 0.3])
w.set_progress(0.5)
print('OK', load_peaks('does_not_exist.json'))
"
```
Expected: prints `OK []`, no traceback.

- [ ] **Step 4: Commit**

```bash
git add ui/widgets/__init__.py ui/widgets/waveform.py
git commit -m "Add WaveformWidget"
```

---

### Task 8: `SoundCard`

**Files:**
- Create: `ui/widgets/sound_card.py`

**Interfaces:**
- Consumes: `get_icon`, `CATEGORY_COLORS`, `TEXT_MAIN`, `TEXT_MUTED`, `BG_APP` from `ui/theme.py` (Task 6); `WaveformWidget`, `load_peaks` from `ui/widgets/waveform.py` (Task 7).
- Produces: `SoundCard(sound: dict, parent=None)` — a `QFrame` exposing `self.sound` (the dict passed in) and `set_playback_progress(ratio: float)`, plus signals `play_requested(str)`, `delete_requested(str)`, `hotkey_requested(str, object)`, `volume_changed(str, int)`, `color_changed(str, str)` (all first arg is `sound["id"]`).

- [ ] **Step 1: Create `ui/widgets/sound_card.py`**

```python
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout

from ui.theme import BG_APP, CATEGORY_COLORS, TEXT_MAIN, TEXT_MUTED, get_icon
from ui.widgets.waveform import WaveformWidget, load_peaks


class SoundCard(QFrame):
    play_requested = Signal(str)
    delete_requested = Signal(str)
    hotkey_requested = Signal(str, object)
    volume_changed = Signal(str, int)
    color_changed = Signal(str, str)

    def __init__(self, sound, parent=None):
        super().__init__(parent)
        self.sound = sound
        self.setObjectName("SoundCard")
        self.setFixedSize(300, 130)
        self._build()

    def _build(self):
        cat = self.sound.get("color", "Gris")
        cat_hex = CATEGORY_COLORS.get(cat, "#8B8D93")
        if cat != "Gris":
            self.setStyleSheet(f"#SoundCard {{ border-left: 4px solid {cat_hex}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)

        top_row = QHBoxLayout()
        name_lbl = QLabel(self.sound.get("name", "Unknown"))
        name_lbl.setStyleSheet(f"font-weight: 600; font-size: 14px; color: {TEXT_MAIN};")
        top_row.addWidget(name_lbl)
        top_row.addStretch()

        self.hk_btn = QPushButton(self.sound.get("hotkey", "None"))
        self.hk_btn.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; background: {BG_APP}; padding: 2px 6px; border-radius: 4px;")
        self.hk_btn.clicked.connect(lambda: self.hotkey_requested.emit(self.sound["id"], self.hk_btn))
        top_row.addWidget(self.hk_btn)

        btn_del = QPushButton()
        btn_del.setIcon(get_icon("delete.svg"))
        btn_del.setProperty("class", "danger")
        btn_del.setFixedSize(28, 28)
        btn_del.clicked.connect(lambda: self.delete_requested.emit(self.sound["id"]))
        top_row.addWidget(btn_del)

        layout.addLayout(top_row)

        self.waveform = WaveformWidget(interactive=False)
        peaks_path = (self.sound.get("filename") or "") + ".peaks.json"
        self.waveform.set_peaks(load_peaks(peaks_path))
        layout.addWidget(self.waveform)

        bot_row = QHBoxLayout()
        btn_play = QPushButton(" PLAY")
        btn_play.setIcon(get_icon("play.svg"))
        btn_play.setProperty("class", "accent")
        btn_play.setFixedSize(85, 26)
        btn_play.clicked.connect(lambda: self.play_requested.emit(self.sound["id"]))
        bot_row.addWidget(btn_play)

        vol_slider = QSlider(Qt.Horizontal)
        vol_slider.setRange(0, 400)
        vol_slider.setValue(self.sound.get("volume", 100))
        vol_slider.setFixedWidth(80)
        vol_slider.sliderReleased.connect(lambda: self.volume_changed.emit(self.sound["id"], vol_slider.value()))
        bot_row.addWidget(vol_slider)

        cb_color = QComboBox()
        cb_color.addItems(list(CATEGORY_COLORS.keys()))
        cb_color.setCurrentText(cat)
        cb_color.setFixedWidth(80)
        cb_color.currentTextChanged.connect(lambda c: self.color_changed.emit(self.sound["id"], c))
        bot_row.addWidget(cb_color)

        layout.addLayout(bot_row)

    def set_playback_progress(self, ratio):
        self.waveform.set_progress(ratio)
```

- [ ] **Step 2: Manual verification**

Run:
```bash
python -c "
from PySide6.QtWidgets import QApplication
from ui.widgets.sound_card import SoundCard
app = QApplication([])
card = SoundCard({'id': 'x1', 'name': 'Test', 'filename': 'nope.wav', 'hotkey': 'f1', 'volume': 100, 'color': 'SFX'})
card.set_playback_progress(0.3)
print('OK')
"
```
Expected: prints `OK`, no traceback.

- [ ] **Step 3: Commit**

```bash
git add ui/widgets/sound_card.py
git commit -m "Add SoundCard widget"
```

---

### Task 9: `PlayerBar`

**Files:**
- Create: `ui/widgets/player_bar.py`

**Interfaces:**
- Consumes: `WaveformWidget` from `ui/widgets/waveform.py` (Task 7).
- Produces: `PlayerBar(parent=None)` — a `QFrame` with `update_progress(name: str, current: float, duration: float, peaks: list[float] | None)` and signal `seek_requested(float)`.

- [ ] **Step 1: Create `ui/widgets/player_bar.py`**

```python
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel

from ui.widgets.waveform import WaveformWidget


class PlayerBar(QFrame):
    seek_requested = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SoundCard")
        self.setFixedHeight(60)
        layout = QHBoxLayout(self)

        self.lbl_playing = QLabel("Aucun son en cours")
        self.lbl_playing.setFixedWidth(250)
        layout.addWidget(self.lbl_playing)

        self.lbl_time_cur = QLabel("0:00")
        self.lbl_time_cur.setFixedWidth(40)
        layout.addWidget(self.lbl_time_cur)

        self.waveform = WaveformWidget(interactive=True)
        self.waveform.seek_requested.connect(self.seek_requested)
        layout.addWidget(self.waveform)

        self.lbl_time_tot = QLabel("0:00")
        self.lbl_time_tot.setFixedWidth(40)
        layout.addWidget(self.lbl_time_tot)

    def update_progress(self, name, current, duration, peaks):
        self.lbl_playing.setText(f"En cours: {name}" if name else "Aucun son en cours")
        self.lbl_time_cur.setText(self._format_time(current))
        self.lbl_time_tot.setText(self._format_time(duration))
        if peaks is not None:
            self.waveform.set_peaks(peaks)
        self.waveform.set_progress(current / duration if duration > 0 else 0.0)

    @staticmethod
    def _format_time(seconds):
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}:{secs:02d}"
```

- [ ] **Step 2: Manual verification**

Run:
```bash
python -c "
from PySide6.QtWidgets import QApplication
from ui.widgets.player_bar import PlayerBar
app = QApplication([])
bar = PlayerBar()
bar.update_progress('Test', 12.5, 30.0, [0.2, 0.8])
print('OK')
"
```
Expected: prints `OK`, no traceback.

- [ ] **Step 3: Commit**

```bash
git add ui/widgets/player_bar.py
git commit -m "Add PlayerBar widget"
```

---

### Task 10: `SettingsView`

Fixes the settings/playback config-key mismatch: the old code saved
`default_device`/`second_device` while playback read
`primary_output`/`secondary_output`, so the secondary device selection
never actually reached playback. This view now writes the same keys
`AudioManager`/`HotkeyManager` read, and adds a real on/off toggle for
dual output plus the fade duration fields.

**Files:**
- Create: `ui/views/__init__.py` (empty)
- Create: `ui/views/settings_view.py`

**Interfaces:**
- Consumes: `TEXT_MAIN` from `ui/theme.py` (Task 6); `AudioManager.get_output_devices() -> list[{"name": str, "id": ...}]` (existing method, unchanged).
- Produces: `SettingsView(audio_manager, config: dict, on_save: Callable[[dict], None], on_bind_panic: Callable[[], None], parent=None)` — a `QWidget` with `set_panic_label(hotkey_text: str)`. Calls `on_save(config)` with the mutated config dict when the user clicks Save (does not call `config_manager.save_config` itself — that's the caller's responsibility, done in `main_window.py`).

- [ ] **Step 1: Create `ui/views/__init__.py`**

Empty file.

- [ ] **Step 2: Create `ui/views/settings_view.py`**

```python
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFrame, QGridLayout, QLabel, QMessageBox,
    QPushButton, QSpinBox, QVBoxLayout, QWidget
)

from ui.theme import TEXT_MAIN


class SettingsView(QWidget):
    def __init__(self, audio_manager, config, on_save, on_bind_panic, parent=None):
        super().__init__(parent)
        self.audio_manager = audio_manager
        self.config = config
        self.on_save = on_save
        self.on_bind_panic = on_bind_panic
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)

        title = QLabel("Réglages Audio")
        title.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {TEXT_MAIN};")
        layout.addWidget(title)

        form = QFrame()
        form.setObjectName("SoundCard")
        form_layout = QGridLayout(form)
        form_layout.setSpacing(20)

        devices = self.audio_manager.get_output_devices()
        dev_list = [d["name"] for d in devices]

        self.cb_main_device = QComboBox()
        self.cb_main_device.addItems(dev_list)
        if self.config.get("primary_output") in dev_list:
            self.cb_main_device.setCurrentText(self.config["primary_output"])

        self.chk_dual = QCheckBox("Activer la double sortie")
        self.chk_dual.setChecked(self.config.get("dual_output_enabled", False))
        self.chk_dual.toggled.connect(self._on_dual_toggled)

        self.cb_second_device = QComboBox()
        self.cb_second_device.addItems(dev_list)
        if self.config.get("secondary_output") in dev_list:
            self.cb_second_device.setCurrentText(self.config["secondary_output"])
        self.cb_second_device.setEnabled(self.chk_dual.isChecked())

        row = 0
        form_layout.addWidget(QLabel("Périphérique Principal :"), row, 0)
        form_layout.addWidget(self.cb_main_device, row, 1)
        row += 1
        form_layout.addWidget(self.chk_dual, row, 0)
        row += 1
        form_layout.addWidget(QLabel("Périphérique Secondaire (Câble Virtuel) :"), row, 0)
        form_layout.addWidget(self.cb_second_device, row, 1)
        row += 1

        self.cb_ducking = QComboBox()
        self.cb_ducking.addItems(["Aucun", "Léger (50%)", "Fort (80%)", "Total (100%)"])
        self.cb_ducking.setCurrentText(self.config.get("audio_ducking_level", "Léger (50%)"))
        form_layout.addWidget(QLabel("Atténuation (Ducking) :"), row, 0)
        form_layout.addWidget(self.cb_ducking, row, 1)
        row += 1

        self.spin_fade_in = QSpinBox()
        self.spin_fade_in.setRange(0, 5000)
        self.spin_fade_in.setSingleStep(50)
        self.spin_fade_in.setValue(self.config.get("fade_in_ms", 150))
        form_layout.addWidget(QLabel("Fondu d'entrée (ms) :"), row, 0)
        form_layout.addWidget(self.spin_fade_in, row, 1)
        row += 1

        self.spin_fade_out = QSpinBox()
        self.spin_fade_out.setRange(0, 5000)
        self.spin_fade_out.setSingleStep(50)
        self.spin_fade_out.setValue(self.config.get("fade_out_ms", 150))
        form_layout.addWidget(QLabel("Fondu de sortie (ms) :"), row, 0)
        form_layout.addWidget(self.spin_fade_out, row, 1)
        row += 1

        self.btn_panic = QPushButton(f"Touche Arrêt: {self.config.get('panic_hotkey', 'None')}")
        self.btn_panic.clicked.connect(self.on_bind_panic)
        form_layout.addWidget(QLabel("Arrêt d'urgence global :"), row, 0)
        form_layout.addWidget(self.btn_panic, row, 1)
        row += 1

        btn_save = QPushButton("SAUVEGARDER")
        btn_save.setProperty("class", "accent")
        btn_save.clicked.connect(self._save)
        form_layout.addWidget(btn_save, row, 1)

        layout.addWidget(form)
        layout.addStretch()

    def _on_dual_toggled(self, checked):
        self.cb_second_device.setEnabled(checked)

    def set_panic_label(self, hotkey_text):
        self.btn_panic.setText(f"Touche Arrêt: {hotkey_text}")

    def _save(self):
        self.config["primary_output"] = self.cb_main_device.currentText()
        self.config["dual_output_enabled"] = self.chk_dual.isChecked()
        self.config["secondary_output"] = self.cb_second_device.currentText()
        self.config["audio_ducking_level"] = self.cb_ducking.currentText()
        self.config["fade_in_ms"] = self.spin_fade_in.value()
        self.config["fade_out_ms"] = self.spin_fade_out.value()
        self.on_save(self.config)
        QMessageBox.information(self, "Succès", "Réglages appliqués.")
```

- [ ] **Step 3: Manual verification**

Run:
```bash
python -c "
from PySide6.QtWidgets import QApplication
from audio_manager import AudioManager
from ui.views.settings_view import SettingsView
app = QApplication([])
view = SettingsView(AudioManager(), {'sounds': []}, lambda c: print('saved', c.get('dual_output_enabled')), lambda: None)
view._save()
"
```
Expected: prints `saved False`, no traceback.

- [ ] **Step 4: Commit**

```bash
git add ui/views/__init__.py ui/views/settings_view.py
git commit -m "Add SettingsView with fixed device keys and dual-output toggle"
```

---

### Task 11: `LibraryView`

Also fixes a YouTube-import bug: the old code called
`download_youtube_audio_async(url, "downloads", prog_cb, done_cb)` with
the callback/progress_callback arguments swapped relative to
`yt_downloader.download_youtube_audio_async`'s actual signature
`(url, output_dir, callback, progress_callback)`, and treated the result
list as dicts (`r['filepath']`) when `yt_downloader.py` actually returns a
list of `(filepath, title)` tuples that are already normalized (it calls
`normalize_and_import_audio` internally) — so the old code was also
silently re-normalizing an already-normalized file through the wrong
accessor. This task calls the download function with the arguments in the
right order and consumes the tuples directly, without a redundant second
normalization pass.

**Files:**
- Create: `ui/views/library_view.py`

**Interfaces:**
- Consumes: `get_icon` from `ui/theme.py` (Task 6); `SoundCard` from `ui/widgets/sound_card.py` (Task 8); `generate_and_save_peaks`, `normalize_and_import_audio` from `audio_processor.py` (Task 3 / existing); `download_youtube_audio_async(url, output_dir, callback, progress_callback)` from `yt_downloader.py` (existing, unchanged).
- Produces: `LibraryView(config: dict, parent=None)` — a `QWidget` exposing `self.sounds: list[dict]`, `self.cards: dict[str, SoundCard]` (keyed by sound id, rebuilt on every `refresh()`), method `refresh()`, and signals `sound_played(dict)`, `hotkey_bind_requested(str, object)`.

- [ ] **Step 1: Create `ui/views/library_view.py`**

```python
import os
import threading
import uuid

from PySide6.QtCore import Qt, QObject, QTimer, Signal, Slot
from PySide6.QtWidgets import (
    QDialog, QFileDialog, QGridLayout, QHBoxLayout, QLineEdit, QMessageBox,
    QProgressBar, QProgressDialog, QPushButton, QScrollArea, QVBoxLayout, QWidget
)

import config_manager
from audio_processor import generate_and_save_peaks, normalize_and_import_audio
from ui.theme import get_icon
from ui.widgets.sound_card import SoundCard
from yt_downloader import download_youtube_audio_async


class LibraryView(QWidget):
    sound_played = Signal(dict)
    hotkey_bind_requested = Signal(str, object)
    add_sound_done = Signal(str, dict)

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.sounds = self.config.get("sounds", [])
        self.filtered_sounds = list(self.sounds)
        self.cards = {}
        self._build()
        self.add_sound_done.connect(self._on_add_sound_done)
        self._rebuild_grid()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        topbar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher un son (Titre, Touche, Catégorie)...")
        self.search_input.setFixedHeight(36)
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._filter_sounds)
        self.search_input.textChanged.connect(lambda _t: self.search_timer.start(300))
        topbar.addWidget(self.search_input)

        btn_add = QPushButton(" IMPORT LOCAL")
        btn_add.setIcon(get_icon("add.svg"))
        btn_add.setFixedHeight(36)
        btn_add.clicked.connect(self.add_sound)
        topbar.addWidget(btn_add)

        btn_yt = QPushButton(" YT DOWNLOAD")
        btn_yt.setIcon(get_icon("download.svg"))
        btn_yt.setProperty("class", "accent")
        btn_yt.setFixedHeight(36)
        btn_yt.clicked.connect(self.download_youtube)
        topbar.addWidget(btn_yt)

        layout.addLayout(topbar)
        layout.addSpacing(10)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.grid_layout = QGridLayout(self.scroll_widget)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(15)
        self.scroll_area.setWidget(self.scroll_widget)
        layout.addWidget(self.scroll_area)

        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self._rebuild_grid)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resize_timer.start(150)

    def refresh(self):
        self.sounds = self.config.get("sounds", [])
        self._filter_sounds()

    def _filter_sounds(self):
        term = self.search_input.text().lower()
        self.filtered_sounds = [
            s for s in self.sounds
            if term in s.get("name", "").lower()
            or term in s.get("hotkey", "").lower()
            or term in s.get("color", "").lower()
        ]
        self._rebuild_grid()

    def _rebuild_grid(self):
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        width = self.scroll_area.viewport().width()
        card_width = 320
        cols = max(1, width // (card_width + 15))

        self.cards = {}
        for i, sound in enumerate(self.filtered_sounds):
            row, col = divmod(i, cols)
            card = SoundCard(sound)
            card.play_requested.connect(self._on_play)
            card.delete_requested.connect(self.remove_sound)
            card.hotkey_requested.connect(self.hotkey_bind_requested)
            card.volume_changed.connect(self._on_volume_changed)
            card.color_changed.connect(self._on_color_changed)
            self.cards[sound["id"]] = card
            self.grid_layout.addWidget(card, row, col)

        self.grid_layout.setRowStretch(self.grid_layout.rowCount(), 1)

    def _on_play(self, sound_id):
        sound = next((s for s in self.sounds if s["id"] == sound_id), None)
        if sound:
            self.sound_played.emit(sound)

    def _on_volume_changed(self, sound_id, value):
        for s in self.sounds:
            if s["id"] == sound_id:
                s["volume"] = value
                break
        self._persist()

    def _on_color_changed(self, sound_id, color):
        for s in self.sounds:
            if s["id"] == sound_id:
                s["color"] = color
                break
        self._persist()
        self.refresh()

    def remove_sound(self, sound_id):
        reply = QMessageBox.question(
            self, "Confirmation", "Êtes-vous sûr de vouloir supprimer ce son ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.No:
            return
        self.sounds = [s for s in self.sounds if s["id"] != sound_id]
        self._persist()
        self.refresh()

    def _persist(self):
        self.config["sounds"] = self.sounds
        config_manager.save_config(self.config)

    def add_sound(self):
        f, _ = QFileDialog.getOpenFileName(
            self, "Sélectionner un fichier audio", "",
            "Audio Files (*.mp3 *.wav *.ogg *.flac *.m4a)"
        )
        if not f:
            return

        sid = str(uuid.uuid4())[:8]
        new_sound = {
            "id": sid, "name": os.path.basename(f), "filename": f,
            "hotkey": "None", "volume": 100, "color": "Gris",
        }

        self.progress_dialog = QProgressDialog("Importation et normalisation en cours...", None, 0, 0, self)
        self.progress_dialog.setWindowTitle("Veuillez patienter")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setCancelButton(None)
        self.progress_dialog.show()

        def process():
            try:
                proc_path = normalize_and_import_audio(f, "downloads", sid)
                generate_and_save_peaks(proc_path)
            except Exception:
                proc_path = None
            self.add_sound_done.emit(proc_path or "", new_sound)

        threading.Thread(target=process, daemon=True).start()

    @Slot(str, dict)
    def _on_add_sound_done(self, proc_path, new_sound):
        if hasattr(self, "progress_dialog") and self.progress_dialog:
            self.progress_dialog.close()

        if proc_path:
            new_sound["filename"] = proc_path
            self.sounds.insert(0, new_sound)
            self._persist()
            self.refresh()
        else:
            QMessageBox.critical(self, "Erreur", "Échec de l'import du fichier audio.")

    def download_youtube(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Télécharger YouTube")
        dlg.setFixedSize(400, 200)

        layout = QVBoxLayout(dlg)
        url_input = QLineEdit()
        url_input.setPlaceholderText("URL YouTube (https://...)")
        layout.addWidget(url_input)

        title_input = QLineEdit()
        title_input.setPlaceholderText("Nom du son (optionnel)")
        layout.addWidget(title_input)

        pb = QProgressBar()
        pb.setValue(0)
        layout.addWidget(pb)

        btn_dl = QPushButton("TÉLÉCHARGER")
        btn_dl.setProperty("class", "accent")
        layout.addWidget(btn_dl)

        class YTSignals(QObject):
            progress = Signal(int)
            done = Signal(bool, list, str)

        sigs = YTSignals()
        sigs.progress.connect(pb.setValue)

        def start_dl():
            url = url_input.text().strip()
            if not url:
                return
            btn_dl.setEnabled(False)

            def prog_cb(pct_str, curr, tot, t):
                try:
                    pct = float(pct_str.replace("%", "").strip())
                    sigs.progress.emit(int(pct))
                except ValueError:
                    pass

            def done_cb(succ, res, err):
                sigs.done.emit(succ, res or [], err)

            download_youtube_audio_async(url, "downloads", done_cb, prog_cb)

        def finish(succ, res, err):
            dlg.accept()
            if succ and res:
                for filepath, yt_title in res:
                    sid = str(uuid.uuid4())[:8]
                    try:
                        generate_and_save_peaks(filepath)
                    except Exception:
                        pass
                    new_sound = {
                        "id": sid, "name": title_input.text() or yt_title,
                        "filename": filepath, "hotkey": "None", "volume": 100,
                        "color": "Musiques",
                    }
                    self.sounds.insert(0, new_sound)
                self._persist()
                self.refresh()
            else:
                QMessageBox.critical(self, "Erreur", f"Échec: {err}")

        sigs.done.connect(finish)
        btn_dl.clicked.connect(start_dl)
        dlg.exec()
```

- [ ] **Step 2: Manual verification**

Run:
```bash
python -c "
from PySide6.QtWidgets import QApplication
from ui.views.library_view import LibraryView
app = QApplication([])
view = LibraryView({'sounds': []})
print('OK', view.sounds, view.cards)
"
```
Expected: prints `OK [] {}`, no traceback.

- [ ] **Step 3: Commit**

```bash
git add ui/views/library_view.py
git commit -m "Add LibraryView, fix YouTube download argument order and double-normalize bug"
```

---

### Task 12: `AppGUI` assembly and app wiring

**Files:**
- Create: `ui/main_window.py`
- Modify: `main.py`
- Delete: `gui_pyside.py`
- Modify: `SidSoundboard.spec`

**Interfaces:**
- Consumes: `QSS`, `TEXT_MAIN`, `get_icon` from `ui/theme.py` (Task 6); `LibraryView` from `ui/views/library_view.py` (Task 11); `SettingsView` from `ui/views/settings_view.py` (Task 10); `PlayerBar` from `ui/widgets/player_bar.py` (Task 9); `load_peaks` from `ui/widgets/waveform.py` (Task 7); `AudioManager.set_fade_durations`, `.toggle_play_pause`, `.seek_focused`, `.get_focused_progress`, `.focused_info`, `.stop_all` (existing/Task 5); `HotkeyManager.shutdown`, `.load_hotkeys` (existing/Task 2); `generate_cached_file_sync` from `audio_processor.py` (existing, unchanged).
- Produces: `AppGUI(audio_manager, hotkey_manager)` — a `QMainWindow`, drop-in replacement for the old `gui_pyside.AppGUI` (same constructor signature, so `main.py` only needs its import changed).

- [ ] **Step 1: Create `ui/main_window.py`**

```python
import threading

import keyboard
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton, QStackedWidget,
    QVBoxLayout, QWidget
)

import config_manager
from audio_processor import generate_cached_file_sync
from ui.theme import QSS, TEXT_MAIN, get_icon
from ui.views.library_view import LibraryView
from ui.views.settings_view import SettingsView
from ui.widgets.player_bar import PlayerBar
from ui.widgets.waveform import load_peaks


class AppGUI(QMainWindow):
    def __init__(self, audio_manager, hotkey_manager):
        super().__init__()
        self.audio_manager = audio_manager
        self.hotkey_manager = hotkey_manager
        self.config = config_manager.load_config()
        self.audio_manager.set_fade_durations(
            self.config.get("fade_in_ms", 150), self.config.get("fade_out_ms", 150)
        )

        self.setWindowTitle("SidSoundboard - Studio Edition")
        self.resize(1050, 750)
        self.setMinimumSize(950, 650)
        self.setStyleSheet(QSS)

        self.timeline_timer = QTimer()
        self.timeline_timer.timeout.connect(self._update_timeline)
        self.timeline_timer.start(100)

        self._build_ui()

    def _build_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(220)
        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setContentsMargins(0, 20, 0, 20)

        title = QLabel("SidSoundboard")
        title.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {TEXT_MAIN}; padding-left: 20px;")
        side_layout.addWidget(title)
        side_layout.addSpacing(30)

        self.btn_lib = QPushButton(" Bibliothèque")
        self.btn_lib.setIcon(get_icon("lib.svg"))
        self.btn_lib.setCheckable(True)
        self.btn_lib.setChecked(True)
        self.btn_lib.clicked.connect(lambda: self._switch_tab(0))

        self.btn_set = QPushButton(" Réglages")
        self.btn_set.setIcon(get_icon("settings.svg"))
        self.btn_set.setCheckable(True)
        self.btn_set.clicked.connect(lambda: self._switch_tab(1))

        side_layout.addWidget(self.btn_lib)
        side_layout.addWidget(self.btn_set)
        side_layout.addStretch()

        btn_stop = QPushButton(" STOP AUDIO")
        btn_stop.setIcon(get_icon("stop.svg"))
        btn_stop.setProperty("class", "danger")
        btn_stop.clicked.connect(self.audio_manager.stop_all)
        side_layout.addWidget(btn_stop)

        main_layout.addWidget(self.sidebar)

        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.addWidget(content_area)

        self.stacked_widget = QStackedWidget()
        content_layout.addWidget(self.stacked_widget)

        self.library_view = LibraryView(self.config)
        self.library_view.sound_played.connect(self._play_sound)
        self.library_view.hotkey_bind_requested.connect(self._bind_hotkey)
        self.stacked_widget.addWidget(self.library_view)

        self.settings_view = SettingsView(
            self.audio_manager, self.config, self._on_settings_saved, self._bind_panic_key
        )
        self.stacked_widget.addWidget(self.settings_view)

        self.player_bar = PlayerBar()
        self.player_bar.seek_requested.connect(self._on_seek)
        content_layout.addWidget(self.player_bar)

    def _switch_tab(self, index):
        self.stacked_widget.setCurrentIndex(index)
        self.btn_lib.setChecked(index == 0)
        self.btn_set.setChecked(index == 1)

    def _play_sound(self, sound):
        original_file = sound.get("filename")
        vol_p = sound.get("volume", 100)
        spd = sound.get("speed", 100)
        global_sec_vol = self.config.get("global_secondary_volume", 100)
        vol_s = int(vol_p * (global_sec_vol / 100.0))

        try:
            filepath_sec = generate_cached_file_sync(original_file, vol_s, spd)
        except Exception:
            filepath_sec = original_file

        self.audio_manager.toggle_play_pause(
            filepath_primary=original_file,
            filepath_secondary=filepath_sec,
            name=sound.get("name", "Unknown"),
            volume=1.0,
            primary_device_name=self.config.get("primary_output"),
            secondary_device_name=self.config.get("secondary_output"),
            dual_enabled=self.config.get("dual_output_enabled", False),
            sound_id=sound.get("id"),
        )

    def _on_seek(self, ratio):
        fi = self.audio_manager.focused_info
        if fi and fi.get("duration"):
            self.audio_manager.seek_focused(ratio * fi["duration"])

    def _update_timeline(self):
        prog = self.audio_manager.get_focused_progress()
        if not prog:
            self.player_bar.update_progress("", 0, 0, None)
            return

        peaks = None
        card = self.library_view.cards.get(prog.get("sound_id"))
        if card:
            peaks_path = (card.sound.get("filename") or "") + ".peaks.json"
            peaks = load_peaks(peaks_path)
            if prog["duration"] > 0:
                card.set_playback_progress(prog["current"] / prog["duration"])

        self.player_bar.update_progress(prog["name"], prog["current"], prog["duration"], peaks)

    def _bind_hotkey(self, sound_id, btn):
        btn.setText("Press key...")

        def capture():
            hk = keyboard.read_hotkey(suppress=False)
            self._apply_hotkey(hk, sound_id)

        self.hotkey_manager.shutdown()
        threading.Thread(target=capture, daemon=True).start()

    def _apply_hotkey(self, hk, sound_id):
        def apply():
            for s in self.library_view.sounds:
                if s["id"] == sound_id:
                    s["hotkey"] = "None" if hk == "esc" else hk
            self.config["sounds"] = self.library_view.sounds
            config_manager.save_config(self.config)
            self.hotkey_manager.load_hotkeys(self.config)
            self.library_view.refresh()
        QTimer.singleShot(0, apply)

    def _bind_panic_key(self):
        self.settings_view.set_panic_label("Appuyez sur une touche...")

        def capture():
            hk = keyboard.read_hotkey(suppress=False)
            self._apply_panic_key(hk)

        self.hotkey_manager.shutdown()
        threading.Thread(target=capture, daemon=True).start()

    def _apply_panic_key(self, hk):
        def apply():
            self.config["panic_hotkey"] = "None" if hk == "esc" else hk
            config_manager.save_config(self.config)
            self.hotkey_manager.load_hotkeys(self.config)
            self.settings_view.set_panic_label(self.config["panic_hotkey"])
        QTimer.singleShot(0, apply)

    def _on_settings_saved(self, config):
        self.config = config
        self.audio_manager.set_fade_durations(
            config.get("fade_in_ms", 150), config.get("fade_out_ms", 150)
        )
        self.hotkey_manager.load_hotkeys(config)
```

- [ ] **Step 2: Update `main.py`'s import**

In `main.py`, change:

```python
from gui_pyside import AppGUI
```

to:

```python
from ui.main_window import AppGUI
```

- [ ] **Step 3: Delete the old monolithic GUI file**

```bash
git rm gui_pyside.py
```

- [ ] **Step 4: Update `SidSoundboard.spec`**

Remove the stale CustomTkinter `datas` entry (the migration to PySide6 left
it behind). In the `Analysis(...)` call, change:

```python
    datas=[('bin', 'bin'), ('icons', 'icons'), ('logo_sq.png', '.'), ('logo.ico', '.'), ('C:/Users/Portable AZBK/AppData/Local/Python/pythoncore-3.14-64/Lib/site-packages/customtkinter', 'customtkinter')],
```

to:

```python
    datas=[('bin', 'bin'), ('icons', 'icons'), ('logo_sq.png', '.'), ('logo.ico', '.')],
```

`SidSoundboard.spec` is gitignored (`*.spec` in `.gitignore`), so this
change is local-only and not committed — but make it so the next build
doesn't fail looking for a removed package.

- [ ] **Step 5: Manual verification — app launches**

Run: `python main.py`
Expected: the window opens showing the new graphite/amber theme, sidebar
with Bibliothèque/Réglages, an empty (or populated, if `config.json`
exists) sound grid, and the player bar at the bottom. No traceback in the
terminal.

- [ ] **Step 6: Commit**

```bash
git add ui/main_window.py main.py
git commit -m "Wire new ui package into main.py, remove gui_pyside.py"
```

---

### Task 13: End-to-end manual verification

**Files:** none (verification only).

- [ ] **Step 1: Run the full automated test suite**

Run: `python -m unittest discover tests -v`
Expected: `OK`, all tests from Tasks 2-4 pass.

- [ ] **Step 2: Manual functional pass**

Run `python main.py` and check each of the following (per the spec's
testing section):
- Import a local audio file → appears in the grid with a visible waveform.
- Play it → waveform in the card and in the player bar fills progressively;
  a short fade-in is audible at the start.
- Click elsewhere on the player bar waveform → playback seeks to that
  position.
- Play a second sound while the first is still playing → the first fades
  out while the second fades in (crossfade), not an abrupt cut.
- Pause/resume the same sound via its Play button.
- Delete a sound → confirmation dialog, then removed from the grid.
- Download a YouTube URL → appears in the grid, named correctly, waveform
  present.
- Bind a hotkey to a sound, close focus from the app (e.g. click on the
  desktop), press the hotkey → the sound plays.
- Set a panic key in Réglages, press it while a sound plays → all audio
  stops immediately.
- In Réglages, enable "Activer la double sortie", pick a secondary device
  (VB-Cable if installed) and Save, then play a sound → audible on both
  devices in sync.
- Resize the main window → the sound grid reflows without visual glitches.

- [ ] **Step 3: Idle resource check**

With the app running and no sound playing, open Windows Task Manager and
confirm CPU usage for the process sits at ~0% and RAM stays close to the
pre-existing baseline (no large regression from the old CustomTkinter
build — some increase from PySide6's own footprint is expected and
acceptable, but there should be no runaway growth over a few minutes of
idle).

- [ ] **Step 4: Build check**

```bash
pyinstaller SidSoundboard.spec
```

Expected: build completes without errors about missing `customtkinter` or
missing `ui` submodules. Launch `dist/SidSoundboard.exe` and repeat a
quick smoke test (open the app, play one sound, close via the tray icon).

- [ ] **Step 5: Final commit (if Task 13 uncovered fixes)**

If any issue was found and fixed during this pass:

```bash
git add -A
git commit -m "Fix issues found during end-to-end verification"
```

If nothing needed fixing, no commit is required for this task.
