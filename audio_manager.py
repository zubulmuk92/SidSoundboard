import array
import miniaudio
import threading
import time

class AudioManager:
    def __init__(self):
        self.devices = miniaudio.Devices()
        self.active_playbacks = []
        self.focused_info = None
        self.fade_in_ms = 0
        self.fade_out_ms = 0
        self.playback_queue = []
        self.play_mode = "overlay"  # Default mode

    def set_fade_durations(self, fade_in_ms, fade_out_ms):
        self.fade_in_ms = fade_in_ms
        self.fade_out_ms = fade_out_ms

    def get_output_devices(self):
        outputs = []
        for p in self.devices.get_playbacks():
            outputs.append({
                "name": p["name"],
                "id": p["id"]
            })
        return outputs

    def _start_playback(self, filepath, device_id, info, seek_offset, sound_id=None):
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
                total_frames = int((info.duration - seek_offset) * info.sample_rate)
                stream = FadingStream(
                    stream, info.sample_rate, info.nchannels,
                    self.fade_in_ms, self.fade_out_ms, total_frames, fade_state
                )

            device.start(stream)

            self.active_playbacks.append((device, stream, fade_state, sound_id))
            self._cleanup_playbacks()
            return device, fade_state
        except Exception:
            return None, None

    def play_sound(self, filepath_primary, filepath_secondary, name, volume=1.0, primary_device_name=None, secondary_device_name=None, dual_enabled=False, seek_offset=0.0, sound_id=None, loop=False):
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
                dev1, fade_state1 = self._start_playback(filepath_primary, primary_id, info, seek_offset, sound_id)

            if dual_enabled and secondary_id and filepath_secondary:
                info_sec = miniaudio.get_file_info(filepath_secondary)
                self._start_playback(filepath_secondary, secondary_id, info_sec, seek_offset, sound_id)

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
                    "loop": loop,
                    "is_paused": False,
                }

        except Exception as e:
            print(f"Erreur Audio: {str(e)}")
            try:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.critical(None, "Erreur Audio", f"Impossible de jouer le son :\n{str(e)}")
            except Exception:
                pass

    def seek_focused(self, time_seconds):
        if not self.focused_info:
            return
            
        fi = self.focused_info
        
        # Stop ONLY the currently focused sound, not everything!
        # Find the playbacks for this sound_id and close them
        remaining = []
        for entry in self.active_playbacks:
            # entry: (device, stream, fade_state, sound_id)
            if entry[3] == fi.get("sound_id") and entry[0] == fi.get("device"):
                self._close_entry(entry)
            else:
                remaining.append(entry)
        self.active_playbacks = remaining
        
        # Re-play with new offset
        self.play_sound(
            filepath_primary=fi["filepath_primary"],
            filepath_secondary=fi["filepath_secondary"],
            name=fi["name"],
            primary_device_name=fi["primary_device_name"],
            secondary_device_name=fi["secondary_device_name"],
            dual_enabled=fi["dual_enabled"],
            seek_offset=time_seconds,
            sound_id=fi["sound_id"],
            loop=fi.get("loop", False)
        )

    def get_focused_progress(self):
        if not self.focused_info:
            return None
        fi = self.focused_info
        
        if fi.get("is_paused"):
            current_t = fi.get("paused_at", 0.0)
            is_running = False
        else:
            if not fi["device"].running:
                if fi.get("loop", False):
                    self.seek_focused(0.0)
                    return self.get_focused_progress()
                if self.playback_queue:
                    self.play_next()
                    return self.get_focused_progress()
                return None
            current_t = (time.time() - fi["start_sys_time"]) + fi["seek_offset"]
            is_running = True
            
        return {
            "sound_id": fi.get("sound_id"),
            "name": fi["name"],
            "current": current_t,
            "duration": fi["duration"],
            "is_paused": fi.get("is_paused", False)
        }

    @staticmethod
    def _close_entry(entry):
        """
        Releases a playback: the device first, then the file stream behind
        it. Closing the stream matters on Windows — while miniaudio still
        holds the file open, FFmpeg cannot overwrite it, which is what made
        editing a sound mid-playback fail.
        """
        device, stream = entry[0], entry[1]
        try:
            device.close()
        except Exception:
            pass
        try:
            stream.close()
        except Exception:
            pass

    def _cleanup_playbacks(self):
        alive = []
        for entry in self.active_playbacks:
            try:
                if entry[0].running:
                    alive.append(entry)
                else:
                    self._close_entry(entry)
            except Exception:
                pass
        self.active_playbacks = alive

    def stop_all(self):
        for entry in self.active_playbacks:
            self._close_entry(entry)
        self.active_playbacks.clear()
        self.focused_info = None

    def stop_sound(self, sound_id):
        """
        Stops only this sound, leaving anything else playing alone. Returns
        True if something was actually stopped. Callers use this before
        re-rendering a sound's cache files, which cannot be overwritten
        while they are being streamed.
        """
        if sound_id is None:
            return False

        remaining = []
        stopped = False
        for entry in self.active_playbacks:
            if entry[3] == sound_id:
                self._close_entry(entry)
                stopped = True
            else:
                remaining.append(entry)
        self.active_playbacks = remaining

        if self.focused_info and self.focused_info.get("sound_id") == sound_id:
            self.focused_info = None
            stopped = True
        return stopped

    def toggle_play_pause(self, filepath_primary, filepath_secondary, name, volume=1.0, primary_device_name=None, secondary_device_name=None, dual_enabled=False, sound_id=None, loop=False):
        if not filepath_primary:
            return
        fi = self.focused_info

        if fi and fi.get("sound_id") == sound_id:
            if fi.get("is_paused"):
                seek = fi.get("paused_at", 0.0)
                self.stop_all()
                self.play_sound(filepath_primary, filepath_secondary, name, volume, primary_device_name, secondary_device_name, dual_enabled, seek, sound_id, loop)
            else:
                prog = self.get_focused_progress()
                if prog:
                    paused_at = prog["current"]
                    for entry in self.active_playbacks:
                        self._close_entry(entry)
                    self.active_playbacks.clear()
                    fi["is_paused"] = True
                    fi["paused_at"] = paused_at
                    self.focused_info = fi
            return

        if fi and (fi.get("is_paused") or (fi.get("device") and getattr(fi["device"], "running", False))):
            if self.play_mode == "queue":
                self.playback_queue.append({
                    "filepath_primary": filepath_primary,
                    "filepath_secondary": filepath_secondary,
                    "name": name,
                    "volume": volume,
                    "primary_device_name": primary_device_name,
                    "secondary_device_name": secondary_device_name,
                    "dual_enabled": dual_enabled,
                    "seek_offset": 0.0,
                    "sound_id": sound_id,
                    "loop": loop
                })
                return
            elif self.play_mode == "overlay":
                # Do not stop_all, just play the new sound. It becomes the focused one.
                self.play_sound(filepath_primary, filepath_secondary, name, volume, primary_device_name, secondary_device_name, dual_enabled, 0.0, sound_id, loop)
                return

        self.stop_all()
        self.play_sound(filepath_primary, filepath_secondary, name, volume, primary_device_name, secondary_device_name, dual_enabled, 0.0, sound_id, loop)

    def play_next(self):
        if self.play_mode == "overlay":
            # Just stop the focused sound
            if self.focused_info:
                self.stop_sound(self.focused_info.get("sound_id"))
            return True
            
        if not self.playback_queue:
            self.stop_all()
            return False
        
        next_sound = self.playback_queue.pop(0)
        self.stop_all()
        self.play_sound(**next_sound)
        return True


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

    def close(self):
        """Forwards to the wrapped generator so the file handle is released."""
        self.source.close()

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
