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

def normalize_and_import_audio(original_file, target_dir, base_name=None):
    """
    Normalise le volume de l'audio (loudnorm) et le convertit en WAV pour un décodage instantané.
    Bloquant, donc à exécuter dans un thread si utilisé par l'UI.
    """
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        
    if not base_name:
        base_name = os.path.basename(original_file).split('.')[0]
        
    import uuid
    import re
    # Clean string to be a safe filename
    safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', base_name)
    target_file = os.path.join(target_dir, f"{safe_name}_{uuid.uuid4().hex[:6]}.wav")
    
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
    # loudnorm filter + convert to 44.1k 16-bit WAV
    cmd = [
        "ffmpeg", "-y", "-i", original_file,
        "-filter:a", "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-ar", "44100", "-ac", "2",
        target_file
    ]
    
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
    if result.returncode != 0:
        err = result.stderr.decode('utf-8', errors='ignore')
        raise Exception(f"Erreur FFmpeg Normalisation: {err}")
        
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
