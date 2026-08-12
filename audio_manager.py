import miniaudio
import time

class AudioManager:
    def __init__(self):
        self.devices = miniaudio.Devices()
        self.active_playbacks = []
        self.focused_info = None
        
    def get_output_devices(self):
        outputs = []
        for p in self.devices.get_playbacks():
            outputs.append({
                "name": p["name"],
                "id": p["id"]
            })
        return outputs

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
            # Lance le premier playback
            dev1 = None
            if filepath_primary:
                info = miniaudio.get_file_info(filepath_primary)
                dev1 = self._start_playback(filepath_primary, primary_id, info, seek_offset)
            
            # Et le deuxieme si le double output est activé
            if dual_enabled and secondary_id and filepath_secondary:
                info_sec = miniaudio.get_file_info(filepath_secondary)
                self._start_playback(filepath_secondary, secondary_id, info_sec, seek_offset)
                
            # Track le son pour la timeline
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
                    "device": dev1
                }
                
        except Exception as e:
            import tkinter.messagebox as messagebox
            messagebox.showerror("Erreur Audio", f"Impossible de jouer le son :\n{str(e)}")

    def _start_playback(self, filepath, device_id, info, seek_offset):
        try:
            device = miniaudio.PlaybackDevice(
                device_id=device_id,
                nchannels=info.nchannels,
                sample_rate=info.sample_rate
            )
            
            seek_frame = int(seek_offset * info.sample_rate)
            stream = miniaudio.stream_file(filepath, seek_frame=seek_frame)
            next(stream) # init generator
            device.start(stream)
            
            self.active_playbacks.append((device, stream))
            self._cleanup_playbacks()
            return device
        except Exception:
            return None

    def seek_focused(self, time_seconds):
        if not self.focused_info:
            return
            
        # Sauvegarder la référence AVANT de faire stop_all
        fi = self.focused_info
        
        # Stop everything playing right now to restart from seek position
        self.stop_all()
        
        # Re-play with new offset
        self.play_sound(
            filepath_primary=fi["filepath_primary"],
            filepath_secondary=fi["filepath_secondary"],
            name=fi["name"],
            primary_device_name=fi["primary_device_name"],
            secondary_device_name=fi["secondary_device_name"],
            dual_enabled=fi["dual_enabled"],
            seek_offset=time_seconds,
            sound_id=fi["sound_id"]
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

    def _cleanup_playbacks(self):
        alive = []
        for item in self.active_playbacks:
            dev = item[0] if isinstance(item, tuple) else item
            try:
                if dev.running:
                    alive.append(item)
                else:
                    dev.close()
            except:
                pass
        self.active_playbacks = alive

    def stop_all(self):
        for item in self.active_playbacks:
            dev = item[0] if isinstance(item, tuple) else item
            try:
                dev.close()
            except:
                pass
        self.active_playbacks.clear()
        self.focused_info = None

    def toggle_play_pause(self, filepath_primary, filepath_secondary, name, volume=1.0, primary_device_name=None, secondary_device_name=None, dual_enabled=False, sound_id=None):
        if not filepath_primary: return
        fi = self.focused_info
        
        if fi and fi.get("sound_id") == sound_id:
            # Même son -> bascule pause/lecture
            if fi.get("is_paused"):
                # Reprise
                seek = fi.get("paused_at", 0.0)
                self.stop_all()
                self.play_sound(filepath_primary, filepath_secondary, name, volume, primary_device_name, secondary_device_name, dual_enabled, seek, sound_id)
            else:
                # Pause
                prog = self.get_focused_progress()
                if prog:
                    paused_at = prog["current"]
                    for item in self.active_playbacks:
                        dev = item[0] if isinstance(item, tuple) else item
                        try: dev.close()
                        except: pass
                    self.active_playbacks.clear()
                    fi["is_paused"] = True
                    fi["paused_at"] = paused_at
                    self.focused_info = fi
            return
            
        # Son différent -> on coupe tout et on lance
        self.stop_all()
        self.play_sound(filepath_primary, filepath_secondary, name, volume, primary_device_name, secondary_device_name, dual_enabled, 0.0, sound_id)
