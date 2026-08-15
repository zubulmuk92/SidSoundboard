import os
import sys
import subprocess
import threading
import json

# Define absolute path to ffmpeg.exe
if hasattr(sys, '_MEIPASS'):
    FFMPEG_PATH = os.path.join(sys._MEIPASS, 'bin', 'win32', 'ffmpeg.exe')
else:
    FFMPEG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bin', 'win32', 'ffmpeg.exe')

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
        FFMPEG_PATH, "-y", "-i", original_file,
        "-filter:a", filter_str,
        target_file
    ]
    
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
    if result.returncode != 0:
        err = result.stderr.decode('utf-8', errors='ignore')
        raise Exception(f"Erreur FFmpeg: {err}")
        
    return target_file

def normalize_and_import_audio(original_file, target_dir, base_name=None):
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
        FFMPEG_PATH, "-y", "-i", original_file,
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
