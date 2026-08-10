import os
import subprocess
import threading
import static_ffmpeg

# S'assurer que ffmpeg est dans le PATH
static_ffmpeg.add_paths()

def process_audio_async(original_file, volume_percent, speed_percent, on_done_callback):
    """
    Crée une copie du fichier avec le volume et la vitesse appliqués via FFmpeg.
    """
    def worker():
        try:
            if volume_percent == 100 and speed_percent == 100:
                on_done_callback(True, original_file, "")
                return
                
            base, ext = os.path.splitext(original_file)
            target_file = f"{base}_v{volume_percent}_s{speed_percent}{ext}"
            
            if os.path.exists(target_file):
                # Déjà mis en cache
                on_done_callback(True, target_file, "")
                return
            
            vol_factor = volume_percent / 100.0
            speed_factor = speed_percent / 100.0
            
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
            filters = []
            if volume_percent != 100:
                filters.append(f"volume={vol_factor}")
            if speed_percent != 100:
                filters.append(f"asetrate=44100*{speed_factor}")
                filters.append("aresample=44100")
                
            filter_str = ",".join(filters)
                
            cmd = [
                "ffmpeg", "-y", "-i", original_file,
                "-filter:a", filter_str,
                target_file
            ]
            
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
            if result.returncode != 0:
                err = result.stderr.decode('utf-8', errors='ignore')
                raise Exception(f"Erreur FFmpeg: {err}")
                
            on_done_callback(True, target_file, "")
            
        except Exception as e:
            on_done_callback(False, "", str(e))
            
    threading.Thread(target=worker, daemon=True).start()
