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

    def play_sound(self, filepath, name, volume=1.0, primary_device_name=None, secondary_device_name=None, dual_enabled=False, seek_offset=0.0):
        if not filepath:
            return
            
        primary_id = None
        secondary_id = None
        
        for dev in self.get_output_devices():
            if dev["name"] == primary_device_name:
                primary_id = dev["id"]
            if dev["name"] == secondary_device_name:
                secondary_id = dev["id"]
                
        try:
            info = miniaudio.get_file_info(filepath)
            
            # Lance le premier playback
            dev1 = self._start_playback(filepath, primary_id, info, seek_offset)
            
            # Et le deuxieme si le double output est activé
            if dual_enabled and secondary_id:
                self._start_playback(filepath, secondary_id, info, seek_offset)
                
            # Track le son pour la timeline
            if dev1:
                self.focused_info = {
                    "filepath": filepath,
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
            filepath=fi["filepath"],
            name=fi["name"],
            primary_device_name=fi["primary_device_name"],
            secondary_device_name=fi["secondary_device_name"],
            dual_enabled=fi["dual_enabled"],
            seek_offset=time_seconds
        )

    def get_focused_progress(self):
        if not self.focused_info:
            return None
        fi = self.focused_info
        if not fi["device"].running:
            return None
            
        current_t = (time.time() - fi["start_sys_time"]) + fi["seek_offset"]
        return {
            "name": fi["name"],
            "current": current_t,
            "duration": fi["duration"]
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
