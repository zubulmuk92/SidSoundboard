import os
import subprocess
import threading
import static_ffmpeg

# S'assurer que ffmpeg est dans le PATH
static_ffmpeg.add_paths()

def generate_cached_file_sync(original_file, vol_pct, speed_percent):
    if vol_pct == 100 and speed_percent == 100:
        return original_file
        
    base, ext = os.path.splitext(original_file)
    target_file = f"{base}_v{vol_pct}_s{speed_percent}{ext}"
    
    if os.path.exists(target_file):
        return target_file
        
    vol_factor = vol_pct / 100.0
    speed_factor = speed_percent / 100.0
    
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
    filters = []
    if vol_pct != 100:
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
        
    return target_file

def process_audio_async(original_file, volume_primary, speed_percent, on_done_callback):
    """
    Crée la copie principale du fichier avec le volume et la vitesse appliqués via FFmpeg.
    La version secondaire sera générée à la volée.
    """
    def worker():
        try:
            target_primary = generate_cached_file_sync(original_file, volume_primary, speed_percent)
            on_done_callback(True, target_primary, "")
        except Exception as e:
            on_done_callback(False, None, str(e))
            
    threading.Thread(target=worker, daemon=True).start()
