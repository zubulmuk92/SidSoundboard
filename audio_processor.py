import os
import sys
import subprocess
import json

# Define absolute path to ffmpeg.exe
if hasattr(sys, '_MEIPASS'):
    FFMPEG_PATH = os.path.join(sys._MEIPASS, 'bin', 'win32', 'ffmpeg.exe')
else:
    FFMPEG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bin', 'win32', 'ffmpeg.exe')

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


EFFECT_NEUTRAL = {"volume": 100, "speed": 100, "bass_boost": 0, "reverb": 0}


def _effect(sound, key):
    """Reads an effect value, treating None/missing as the neutral value."""
    value = sound.get(key)
    return EFFECT_NEUTRAL[key] if value is None else value


def build_effects_filter_chain(sound):
    """
    Builds the FFmpeg -filter:a chain for a sound's effects. Neutral
    effects are omitted so an untouched sound renders as a stream copy.
    Volume comes last, to normalize the level after bass/reverb have had
    their chance to push the signal into clipping.
    """
    filters = []

    bass = _effect(sound, "bass_boost")
    if bass > 0:
        filters.append(f"bass=g={round(bass * 0.2, 2)}")

    speed = _effect(sound, "speed")
    if speed != 100:
        filters.append(f"asetrate=44100*{round(speed / 100.0, 4)}")
        filters.append("aresample=44100")

    reverb = _effect(sound, "reverb")
    if reverb > 0:
        delay = int(round(40 + reverb * 1.6))
        decay = round(0.3 + reverb * 0.004, 3)
        filters.append(f"aecho=0.8:0.9:{delay}:{decay}")

    volume = _effect(sound, "volume")
    if volume != 100:
        filters.append(f"volume={round(volume / 100.0, 4)}")

    if filters:
        # Bass boost, reverb and a volume above 100% all push the signal past
        # full scale. Hard clipping there sounds like distortion, so the chain
        # ends on a limiter — free at playback time, since this is baked in.
        # level=disabled: the filter auto-normalizes back to full scale
        # otherwise, which would undo the very headroom it just made.
        filters.append("alimiter=limit=0.95:level=disabled")

    return ",".join(filters)


def build_effects_ffmpeg_args(sound, source, target):
    """FFmpeg argv (without the binary path) rendering `source` to `target`."""
    args = ["-y"]
    trimmed = False

    trim_start = sound.get("trim_start_sec") or 0
    if trim_start > 0:
        args += ["-ss", str(round(float(trim_start), 3))]
        trimmed = True

    trim_end = sound.get("trim_end_sec")
    if trim_end:
        args += ["-to", str(round(float(trim_end), 3))]
        trimmed = True

    args += ["-i", source]

    chain = build_effects_filter_chain(sound)
    if chain:
        args += ["-filter:a", chain]
    elif trimmed:
        # A stream copy can only cut on packet boundaries, overshooting the
        # requested cut by tens of milliseconds. Re-encoding the PCM makes
        # the trim sample-accurate, which is what dragging a handle implies.
        args += ["-c:a", "pcm_s16le"]
    else:
        # Nothing to compute: PCM stream copy, near-instant and lossless.
        args += ["-c", "copy"]

    args.append(target)
    return args


def generate_effects_cache(sound, target_dir=None, suffix="_fx", with_peaks=True):
    """
    Renders every active effect of `sound` into a single deterministic file
    ({id}{suffix}.wav), always overwritten. The source is always
    sound["filename"] — the untouched normalized original — so effects and
    trim stay non-destructive and fully reversible.
    """
    source = sound.get("filename")
    if not source or not os.path.exists(source):
        raise ValueError(f"Fichier source introuvable: {source}")

    if not target_dir:
        target_dir = os.path.dirname(os.path.abspath(source))
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    target = os.path.abspath(
        os.path.join(target_dir, f"{sound.get('id', 'sound')}{suffix}.wav")
    )

    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    cmd = [FFMPEG_PATH] + build_effects_ffmpeg_args(sound, source, target)
    result = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo
    )
    if result.returncode != 0:
        err = result.stderr.decode('utf-8', errors='ignore')
        raise Exception(f"Erreur FFmpeg Effets: {err}")

    if with_peaks:
        try:
            generate_and_save_peaks(target)
        except Exception:
            pass

    return target


def resolve_playback_file(sound):
    """
    The file playback should stream: the effects cache when it is on disk,
    the original otherwise (cache deleted by hand, or sound imported before
    the effects pipeline existed).
    """
    cached = sound.get("cached_effects_file")
    if cached and os.path.exists(cached):
        return cached
    return sound.get("filename")


def resolve_secondary_file(sound):
    """
    The file the virtual-cable output should stream: the attenuated variant
    when one exists, otherwise the same file as the headphones — the two
    routes carry identical effects, and differ only by that attenuation.
    """
    cached = sound.get("cached_secondary_file")
    if cached and os.path.exists(cached):
        return cached
    return resolve_playback_file(sound)


def generate_secondary_cache(sound, secondary_volume, target_dir=None):
    """
    Renders the virtual-cable variant of a sound: the very same baked
    effects, attenuated by the global secondary volume. Returns None at
    100%, where the headphone render already is the right file.

    Pre-rendering this matters: attenuating at play time would mean a
    synchronous FFmpeg run on the first click of every sound, freezing the
    UI — the opposite of the zero-latency design.
    """
    if secondary_volume == 100:
        return None

    source = resolve_playback_file(sound)
    if not source or not os.path.exists(source):
        raise ValueError(f"Fichier source introuvable: {source}")

    if not target_dir:
        target_dir = os.path.dirname(os.path.abspath(source))
    target = os.path.abspath(
        os.path.join(target_dir, f"{sound.get('id', 'sound')}_sec.wav")
    )

    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    cmd = [
        FFMPEG_PATH, "-y", "-i", source,
        "-filter:a", f"volume={round(secondary_volume / 100.0, 4)}",
        target,
    ]
    result = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo
    )
    if result.returncode != 0:
        err = result.stderr.decode('utf-8', errors='ignore')
        raise Exception(f"Erreur FFmpeg Sortie secondaire: {err}")

    return target


def ensure_caches(sound, config, target_dir=None):
    """
    Renders whatever cache files this sound is missing or has outdated, and
    returns True when anything was written. Safe to call on every sound at
    startup: a sound whose caches are all current costs one os.path.exists
    per cache and nothing else.
    """
    changed = False

    cached_fx = sound.get("cached_effects_file")
    if not cached_fx or not os.path.exists(cached_fx):
        sound["cached_effects_file"] = generate_effects_cache(sound, target_dir)
        changed = True

    wanted_volume = config.get("global_secondary_volume", 100)
    cached_sec = sound.get("cached_secondary_file")
    stale = (
        sound.get("cached_secondary_volume") != wanted_volume
        or (cached_sec and not os.path.exists(cached_sec))
    )

    if wanted_volume == 100:
        if cached_sec is not None or "cached_secondary_file" not in sound:
            sound["cached_secondary_file"] = None
            sound["cached_secondary_volume"] = 100
            changed = changed or cached_sec is not None
    elif stale or not cached_sec:
        sound["cached_secondary_file"] = generate_secondary_cache(
            sound, wanted_volume, target_dir
        )
        sound["cached_secondary_volume"] = wanted_volume
        changed = True

    return changed
