import sys
import os
import shutil

# mock the config and things
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from audio_processor import normalize_and_import_audio

# Create a dummy wav file
import wave
dummy_wav = "dummy.wav"
with wave.open(dummy_wav, "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(44100)
    w.writeframes(b'\x00\x00' * 44100)

try:
    print("Testing normalize_and_import_audio...")
    res = normalize_and_import_audio(dummy_wav, "downloads", "test_id")
    print("SUCCESS! File created at:", res)
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    if os.path.exists(dummy_wav):
        os.remove(dummy_wav)
