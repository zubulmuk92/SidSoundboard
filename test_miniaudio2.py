import miniaudio
import sys

def test():
    try:
        devices = miniaudio.Devices()
        outputs = devices.get_playbacks()
        print("Outputs:", [o['name'] for o in outputs])
        
        filepath = "test2.ogg"
        # Just create a small file to test, or we'll ask user what file they play
        print("Miniaudio version:", miniaudio.__version__)
    except Exception as e:
        print("ERROR:", e)

if __name__ == "__main__":
    test()
