import sys
import os

sys.path.append(os.getcwd())
from audio_manager import AudioManager

am = AudioManager()
am.play_sound("C:/Windows/Media/tada.wav", None, "tada")
import time
time.sleep(2)
print("done")
