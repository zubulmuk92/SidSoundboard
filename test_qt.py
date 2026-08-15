import miniaudio
import time
from PySide6.QtWidgets import QApplication, QMainWindow

def test():
    app = QApplication([])
    window = QMainWindow()
    window.show()
    
    # Try playing a file
    filepath = "test2.ogg" # Wait, I don't have a test audio file here. Let's create one or just use a known file.
    
    # Let's see if we have sounds in config.json
    import json
    try:
        with open("config.json", "r") as f:
            cfg = json.load(f)
            sounds = cfg.get("sounds", [])
            if sounds:
                filepath = sounds[0]["filepath"]
                print("Testing with:", filepath)
                
                info = miniaudio.get_file_info(filepath)
                dev = miniaudio.PlaybackDevice(nchannels=info.nchannels, sample_rate=info.sample_rate)
                stream = miniaudio.stream_file(filepath)
                next(stream)
                dev.start(stream)
                
                # Check status for a few seconds
                for i in range(10):
                    QApplication.processEvents()
                    print(f"Running: {dev.running}")
                    time.sleep(0.5)
    except Exception as e:
        print("ERROR:", e)

if __name__ == "__main__":
    test()
